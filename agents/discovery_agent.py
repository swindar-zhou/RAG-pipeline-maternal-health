"""
Agentic Phase 1 Discovery with tools and state management.

Implements a state machine: SEED → SEARCH → SCORE → FETCH → CLASSIFY → VERIFY → DONE/RETRY
"""

import os
import re
import json
import time
import requests
from typing import List, Dict, Optional, Set, Tuple
from enum import Enum
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from schemas.discovery import DiscoveryResult, ProgramLink


class DiscoveryState(Enum):
    """States in the discovery agent workflow."""
    SEED = "seed"              # Starting point
    SEARCH = "search"          # Searching for health department
    SCORE = "score"           # Scoring links
    FETCH = "fetch"           # Fetching page content
    CLASSIFY = "classify"     # Classifying if page is relevant
    VERIFY = "verify"         # Verifying page has required signals
    DONE = "done"            # Completed
    RETRY = "retry"          # Retry with different approach


@dataclass
class AgentState:
    """State tracked per county during discovery."""
    county_name: str
    county_url: str
    current_state: DiscoveryState = DiscoveryState.SEED
    visited_urls: Set[str] = field(default_factory=set)
    candidate_links: List[ProgramLink] = field(default_factory=list)
    health_dept_url: str = ""
    maternal_section_url: str = ""
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    failures: List[str] = field(default_factory=list)
    max_iterations: int = 10
    iteration_count: int = 0


class DiscoveryAgent:
    """
    Agentic discovery system with tools for search, scoring, classification, and verification.
    """
    
    def __init__(
        self,
        timeout: int = 20,
        delay: float = 2.0,
        max_pages: int = 50
    ):
        self.timeout = timeout
        self.delay = delay
        self.max_pages = max_pages
        
        # Keywords for scoring
        self.health_keywords = [
            "health", "public health", "hhsa", "health department",
            "medical", "healthcare", "wellness"
        ]
        self.maternal_keywords = [
            "maternal", "child", "mch", "mcah", "women", "infant",
            "wic", "prenatal", "pregnancy", "family"
        ]
        self.program_keywords = [
            "wic", "healthy start", "home visiting", "nurse family partnership",
            "black infant health", "bih", "maternal", "prenatal", "postpartum"
        ]
    
    def tool_search_health_dept(self, state: AgentState) -> List[str]:
        """Tool 1: Search for health department links on county homepage."""
        if state.county_url in state.visited_urls:
            return []
        
        try:
            response = requests.get(state.county_url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            links = []
            for a in soup.find_all('a', href=True):
                href = urljoin(state.county_url, a['href'])
                text = a.get_text(strip=True).lower()
                
                # Check if link matches health keywords
                if any(keyword in text for keyword in self.health_keywords):
                    links.append(href)
            
            state.visited_urls.add(state.county_url)
            return list(set(links))[:10]  # Top 10 unique links
            
        except Exception as e:
            state.failures.append(f"Search failed: {e}")
            return []
    
    def tool_score_link(self, url: str, link_text: str, nav_path: str) -> float:
        """Tool 2: Score a link based on keywords."""
        score = 0.0
        text_lower = (link_text + " " + url).lower()
        
        # Health department level
        if any(kw in text_lower for kw in self.health_keywords):
            score += 2.0
        
        # Maternal/child level
        if any(kw in text_lower for kw in self.maternal_keywords):
            score += 3.0
        
        # Program level
        if any(kw in text_lower for kw in self.program_keywords):
            score += 5.0
        
        # Penalize external links
        parsed = urlparse(url)
        base_domain = urlparse(nav_path.split(" → ")[0] if " → " in nav_path else url).netloc
        if parsed.netloc and parsed.netloc != base_domain:
            score -= 2.0
        
        return max(0.0, score)
    
    def tool_classify_page(self, url: str, content: str) -> Tuple[bool, float]:
        """Tool 3: Classify if a page is a maternal health program page."""
        content_lower = content.lower()
        
        # Check for program indicators
        program_indicators = sum(
            1 for kw in self.program_keywords if kw in content_lower
        )
        
        # Check for eligibility/apply signals
        has_eligibility = any(
            word in content_lower for word in
            ["eligibility", "qualify", "requirements", "who can"]
        )
        has_apply = any(
            word in content_lower for word in
            ["apply", "application", "how to", "enroll", "register"]
        )
        
        # Classification score
        score = (
            program_indicators * 2.0 +
            (3.0 if has_eligibility else 0.0) +
            (3.0 if has_apply else 0.0)
        )
        
        is_program_page = score >= 5.0
        return is_program_page, score
    
    def tool_verify_signals(self, content: str, contacts: Dict) -> Tuple[bool, List[str]]:
        """Tool 4: Verify page has required signals (eligibility, apply, contact)."""
        content_lower = content.lower()
        signals_found = []
        missing_signals = []
        
        # Check for eligibility
        if any(word in content_lower for word in ["eligibility", "qualify", "requirements"]):
            signals_found.append("eligibility")
        else:
            missing_signals.append("eligibility")
        
        # Check for apply/application
        if any(word in content_lower for word in ["apply", "application", "how to", "enroll"]):
            signals_found.append("apply")
        else:
            missing_signals.append("apply")
        
        # Check for contact
        has_contact = bool(contacts.get("phones") or contacts.get("emails"))
        if has_contact:
            signals_found.append("contact")
        else:
            missing_signals.append("contact")
        
        # Page is verified if it has at least 2/3 signals
        is_verified = len(signals_found) >= 2
        return is_verified, missing_signals
    
    def fetch_page_content(self, url: str) -> Optional[Tuple[str, Dict]]:
        """Fetch page content and extract contacts."""
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract main text (remove nav/header/footer)
            for tag in soup(['nav', 'header', 'footer', 'script', 'style']):
                tag.decompose()
            
            text = soup.get_text(separator=' ', strip=True)
            text = re.sub(r'\s+', ' ', text)[:5000]  # Limit text
            
            # Extract contacts
            phones = re.findall(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
            
            contacts = {
                "phones": list(set(phones))[:5],
                "emails": list(set(emails))[:5]
            }
            
            return text, contacts
            
        except Exception as e:
            return None
    
    def run(self, county_name: str, county_url: str) -> DiscoveryResult:
        """
        Run agentic discovery for a county.
        
        State machine: SEED → SEARCH → SCORE → FETCH → CLASSIFY → VERIFY → DONE
        """
        state = AgentState(county_name=county_name, county_url=county_url)
        
        while state.current_state != DiscoveryState.DONE and state.iteration_count < state.max_iterations:
            state.iteration_count += 1
            
            if state.current_state == DiscoveryState.SEED:
                state.current_state = DiscoveryState.SEARCH
            
            elif state.current_state == DiscoveryState.SEARCH:
                # Search for health department
                health_links = self.tool_search_health_dept(state)
                
                if health_links:
                    # Score and pick best
                    scored = [
                        (link, self.tool_score_link(link, "", state.county_url))
                        for link in health_links
                    ]
                    scored.sort(key=lambda x: x[1], reverse=True)
                    
                    if scored:
                        state.health_dept_url = scored[0][0]
                        state.current_state = DiscoveryState.SCORE
                    else:
                        state.current_state = DiscoveryState.DONE
                else:
                    state.current_state = DiscoveryState.RETRY
            
            elif state.current_state == DiscoveryState.SCORE:
                # Score links from health department page
                if not state.health_dept_url:
                    state.current_state = DiscoveryState.DONE
                    continue
                
                if state.health_dept_url in state.visited_urls:
                    state.current_state = DiscoveryState.DONE
                    continue
                
                content_result = self.fetch_page_content(state.health_dept_url)
                if not content_result:
                    state.current_state = DiscoveryState.DONE
                    continue
                
                content, _ = content_result
                state.visited_urls.add(state.health_dept_url)
                
                # Find links on health dept page
                try:
                    response = requests.get(state.health_dept_url, timeout=self.timeout)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    for a in soup.find_all('a', href=True):
                        href = urljoin(state.health_dept_url, a['href'])
                        link_text = a.get_text(strip=True)
                        nav_path = f"{state.county_url} → Health Dept"
                        
                        score = self.tool_score_link(href, link_text, nav_path)
                        
                        if score > 0:
                            state.candidate_links.append(ProgramLink(
                                name=link_text or href,
                                url=href,
                                link_text=link_text,
                                nav_path=nav_path,
                                score=score
                            ))
                    
                    # Sort by score
                    state.candidate_links.sort(key=lambda x: x.score or 0, reverse=True)
                    state.current_state = DiscoveryState.FETCH
                    
                except Exception as e:
                    state.failures.append(f"Scoring failed: {e}")
                    state.current_state = DiscoveryState.DONE
            
            elif state.current_state == DiscoveryState.FETCH:
                # Fetch top candidate pages
                if not state.candidate_links:
                    state.current_state = DiscoveryState.DONE
                    continue
                
                # Process top K candidates
                top_k = min(10, len(state.candidate_links))
                verified_links = []
                
                for link in state.candidate_links[:top_k]:
                    if link.url in state.visited_urls:
                        continue
                    
                    content_result = self.fetch_page_content(link.url)
                    if not content_result:
                        continue
                    
                    content, contacts = content_result
                    state.visited_urls.add(link.url)
                    
                    # Classify
                    is_program, class_score = self.tool_classify_page(link.url, content)
                    
                    if is_program:
                        # Verify
                        is_verified, missing = self.tool_verify_signals(content, contacts)
                        
                        if is_verified:
                            verified_links.append(link)
                        else:
                            # Still add if high classification score
                            if class_score >= 7.0:
                                verified_links.append(link)
                    
                    time.sleep(self.delay)
                
                # Update candidate links to only verified ones
                state.candidate_links = verified_links[:20]  # Keep top 20
                state.current_state = DiscoveryState.DONE
            
            elif state.current_state == DiscoveryState.RETRY:
                # Retry with different approach (simplified)
                state.current_state = DiscoveryState.DONE
            
            time.sleep(self.delay)
        
        # Build result
        return DiscoveryResult(
            county_name=state.county_name,
            county_url=state.county_url,
            health_dept_url=state.health_dept_url,
            maternal_section_url=state.maternal_section_url,
            programs=state.candidate_links,
            discovered_at=None
        )


def run_agentic_discovery_for_county(county_name: str, county_url: str) -> DiscoveryResult:
    """Convenience function to run agentic discovery."""
    agent = DiscoveryAgent()
    return agent.run(county_name, county_url)

