#!/usr/bin/env python3
"""
Burp Suite Log Analyzer for HubSpot
Analyzes Burp logs to find interesting patterns and potential vulnerabilities
"""

import json
import re
from collections import defaultdict
from typing import List, Dict, Set

class BurpLogAnalyzer:
    def __init__(self, burp_log_file: str):
        self.log_file = burp_log_file
        self.entries = []
        self.portal_ids = set()
        self.api_endpoints = defaultdict(int)
        self.parameters = defaultdict(set)
        
    def load_log(self):
        """Load Burp Suite proxy history or Logger++ export"""
        print(f"[*] Loading log file: {self.log_file}")
        
        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
                # Try to parse as JSON (Logger++ export)
                try:
                    self.entries = json.loads(content)
                    print(f"[+] Loaded {len(self.entries)} entries from JSON")
                except:
                    # Parse as text log
                    self.entries = self._parse_text_log(content)
                    print(f"[+] Loaded {len(self.entries)} entries from text")
                    
        except Exception as e:
            print(f"[!] Error loading log: {str(e)}")
            
    def _parse_text_log(self, content: str) -> List[Dict]:
        """Parse text-based log format"""
        entries = []
        # Basic parsing - adjust based on your log format
        lines = content.split('\n')
        for line in lines:
            if 'hubspot.com' in line.lower() or 'hubapi.com' in line.lower():
                entries.append({'raw': line})
        return entries
    
    def extract_portal_ids(self):
        """Extract all portal IDs from requests"""
        print("\n[*] Extracting portal IDs...")
        
        portal_pattern = re.compile(r'(?:portalId|hubId|portal_id)["\s:=]+(\d+)', re.IGNORECASE)
        
        for entry in self.entries:
            content = str(entry)
            matches = portal_pattern.findall(content)
            self.portal_ids.update(matches)
        
        print(f"[+] Found {len(self.portal_ids)} unique portal IDs:")
        for pid in sorted(self.portal_ids):
            print(f"    - {pid}")
            if pid == '46962361':
                print("      ⭐ CTF CHALLENGE PORTAL!")
    
    def extract_api_endpoints(self):
        """Extract and count API endpoint patterns"""
        print("\n[*] Extracting API endpoints...")
        
        url_pattern = re.compile(r'(https?://[^\s]+)', re.IGNORECASE)
        
        for entry in self.entries:
            content = str(entry)
            urls = url_pattern.findall(content)
            
            for url in urls:
                # Extract path
                match = re.search(r'https?://[^/]+(/[^?\s]*)', url)
                if match:
                    path = match.group(1)
                    # Normalize: remove IDs
                    normalized = re.sub(r'/\d+', '/{id}', path)
                    self.api_endpoints[normalized] += 1
        
        print(f"[+] Found {len(self.api_endpoints)} unique API patterns:")
        # Show top 20
        for endpoint, count in sorted(self.api_endpoints.items(), 
                                      key=lambda x: x[1], 
                                      reverse=True)[:20]:
            print(f"    [{count:4d}] {endpoint}")
    
    def extract_parameters(self):
        """Extract parameters used in requests"""
        print("\n[*] Extracting parameters...")
        
        # Query parameters
        query_pattern = re.compile(r'[?&]([^=&]+)=')
        # JSON parameters
        json_pattern = re.compile(r'"([^"]+)"\s*:')
        
        for entry in self.entries:
            content = str(entry)
            
            # Query params
            query_params = query_pattern.findall(content)
            for param in query_params:
                self.parameters['query'].add(param)
            
            # JSON params
            json_params = json_pattern.findall(content)
            for param in json_params:
                if len(param) < 50:  # Avoid long values
                    self.parameters['json'].add(param)
        
        print(f"[+] Found parameters:")
        print(f"    Query parameters: {len(self.parameters['query'])}")
        print(f"    JSON parameters: {len(self.parameters['json'])}")
        
        # Show interesting parameters
        interesting = ['portalId', 'hubId', 'vid', 'email', 'userId', 
                      'objectId', 'contactId', 'companyId', 'dealId',
                      'firstname', 'super_secret', 'properties']
        
        found_interesting = []
        for param_type in ['query', 'json']:
            for param in self.parameters[param_type]:
                if any(i.lower() in param.lower() for i in interesting):
                    found_interesting.append((param_type, param))
        
        if found_interesting:
            print("\n[!] Interesting parameters found:")
            for ptype, param in found_interesting:
                print(f"    [{ptype}] {param}")
    
    def find_potential_idor(self):
        """Look for potential IDOR patterns"""
        print("\n[*] Searching for potential IDOR patterns...")
        
        findings = []
        
        for entry in self.entries:
            content = str(entry)
            
            # Look for different portal IDs in same session
            portal_matches = re.findall(r'portalId["\s:=]+(\d+)', content, re.IGNORECASE)
            if len(set(portal_matches)) > 1:
                findings.append({
                    'type': 'Multiple portal IDs in request',
                    'details': f"Portal IDs: {set(portal_matches)}"
                })
            
            # Look for object IDs
            if re.search(r'/contact/vid/(\d+)', content):
                if '46962361' in content:
                    findings.append({
                        'type': 'CTF portal contact access attempt',
                        'details': content[:200]
                    })
        
        if findings:
            print(f"[!] Found {len(findings)} potential IDOR patterns:")
            for finding in findings[:10]:  # Show first 10
                print(f"    - {finding['type']}")
                print(f"      {finding['details'][:100]}")
        else:
            print("[-] No obvious IDOR patterns found")
    
    def find_sensitive_data(self):
        """Look for sensitive data in responses"""
        print("\n[*] Searching for sensitive data...")
        
        sensitive_patterns = [
            (r'firstname["\s:]+([^",\s]+)', 'firstname'),
            (r'super_secret["\s:]+([^",\s]+)', 'super_secret'),
            (r'email["\s:]+([^",\s]+@[^",\s]+)', 'email'),
            (r'api[_-]?key["\s:]+([^",\s]+)', 'api_key'),
            (r'token["\s:]+([^",\s]{20,})', 'token'),
        ]
        
        findings = defaultdict(list)
        
        for entry in self.entries:
            content = str(entry)
            
            for pattern, name in sensitive_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    for match in matches[:3]:  # Limit per entry
                        findings[name].append(match)
        
        if findings:
            print("[!] Sensitive data found:")
            for data_type, values in findings.items():
                print(f"    {data_type}: {len(values)} occurrences")
                if data_type in ['firstname', 'super_secret']:
                    print(f"      ⭐ Potential CTF flag!")
                    for val in set(values):
                        print(f"         {val}")
        else:
            print("[-] No sensitive data patterns found")
    
    def generate_report(self, output_file: str):
        """Generate analysis report"""
        print(f"\n[*] Generating report: {output_file}")
        
        with open(output_file, 'w') as f:
            f.write("# Burp Suite Log Analysis Report\n\n")
            
            f.write("## Summary\n")
            f.write(f"- Total entries: {len(self.entries)}\n")
            f.write(f"- Portal IDs found: {len(self.portal_ids)}\n")
            f.write(f"- Unique API endpoints: {len(self.api_endpoints)}\n\n")
            
            f.write("## Portal IDs\n")
            for pid in sorted(self.portal_ids):
                f.write(f"- {pid}\n")
                if pid == '46962361':
                    f.write("  - ⭐ CTF Challenge Portal\n")
            
            f.write("\n## Top API Endpoints\n")
            for endpoint, count in sorted(self.api_endpoints.items(), 
                                         key=lambda x: x[1], 
                                         reverse=True)[:30]:
                f.write(f"- [{count}] {endpoint}\n")
            
            f.write("\n## Parameters\n")
            f.write("### Query Parameters\n")
            for param in sorted(self.parameters['query']):
                f.write(f"- {param}\n")
            
            f.write("\n### JSON Parameters\n")
            for param in sorted(self.parameters['json'])[:50]:
                f.write(f"- {param}\n")
        
        print(f"[+] Report saved to {output_file}")


def main():
    print("="*60)
    print("Burp Suite Log Analyzer for HubSpot")
    print("="*60)
    print()
    
    log_file = input("Enter path to Burp log file: ").strip()
    
    analyzer = BurpLogAnalyzer(log_file)
    analyzer.load_log()
    
    if not analyzer.entries:
        print("[!] No entries loaded. Check your log file.")
        return
    
    # Run analyses
    analyzer.extract_portal_ids()
    analyzer.extract_api_endpoints()
    analyzer.extract_parameters()
    analyzer.find_potential_idor()
    analyzer.find_sensitive_data()
    
    # Generate report
    output = input("\nGenerate report? (y/n): ").strip().lower()
    if output == 'y':
        report_file = input("Enter output filename (default: analysis-report.md): ").strip()
        if not report_file:
            report_file = "analysis-report.md"
        analyzer.generate_report(report_file)
    
    print("\n[*] Analysis complete!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
