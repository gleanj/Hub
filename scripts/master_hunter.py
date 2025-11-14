#!/usr/bin/env python3
"""
Master CTF Hunter - Orchestrates all testing tools
The ultimate automation for finding the $15,000 HubSpot CTF flag
"""

import subprocess
import sys
import os
import json
from datetime import datetime
import argparse

class MasterHunter:
    def __init__(self, api_key: str = None, cookies: str = None):
        self.api_key = api_key
        self.cookies = cookies
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.results = {
            'started': datetime.now().isoformat(),
            'tools_run': [],
            'findings': []
        }

    def banner(self):
        """Display banner"""
        print("="*70)
        print("""
         
                 
                
        """)
        print("Target: Portal 46962361 | Bounty: $15,000 + $5,000 bonus")
        print("="*70)
        print()

    def run_automated_scanner(self):
        """Run the main automated scanner"""
        print("[*] Running Automated Scanner...")
        print("    Testing: Direct access, batch ops, search, pollution, etc.")
        print()

        if not self.api_key:
            print("[!] API key required for automated scanner")
            return

        # Build command
        cmd = ['python3', f'{self.script_dir}/ctf_automated_scanner.py']

        # Run interactively
        try:
            env = os.environ.copy()
            env['HUBSPOT_API_KEY'] = self.api_key
            if self.cookies:
                env['HUBSPOT_COOKIES'] = self.cookies

            # Create input for the script
            user_input = f"{self.api_key}\n"
            if self.cookies:
                user_input += f"y\n{self.cookies}\n"
            else:
                user_input += "n\n"

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            output, _ = process.communicate(input=user_input, timeout=300)
            print(output)

            self.results['tools_run'].append('automated_scanner')

            # Check for findings
            if 'INTERESTING FINDINGS' in output:
                print("\n[!!!] AUTOMATED SCANNER FOUND SOMETHING INTERESTING!")
                self.results['findings'].append({
                    'tool': 'automated_scanner',
                    'note': 'Check scan results file'
                })

        except subprocess.TimeoutExpired:
            print("[!] Automated scanner timeout (>5 minutes)")
        except Exception as e:
            print(f"[!] Error running automated scanner: {e}")

    def run_graphql_tester(self):
        """Run GraphQL introspection and testing"""
        print("\n[*] Running GraphQL Introspection...")
        print("    Testing: Schema introspection, contact queries, mutations")
        print()

        if not self.cookies:
            print("[!] Session cookies required for GraphQL testing")
            print("[!] Skipping GraphQL tests")
            return

        cmd = ['python3', f'{self.script_dir}/graphql_introspection.py']

        try:
            user_input = f"{self.cookies}\n"

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            output, _ = process.communicate(input=user_input, timeout=180)
            print(output)

            self.results['tools_run'].append('graphql_tester')

            # Check for success
            if 'SUCCESS' in output or 'POTENTIAL FLAG' in output:
                print("\n[!!!] GRAPHQL TESTER FOUND SOMETHING!")
                self.results['findings'].append({
                    'tool': 'graphql_tester',
                    'note': 'Check output above'
                })

        except subprocess.TimeoutExpired:
            print("[!] GraphQL tester timeout")
        except Exception as e:
            print(f"[!] Error running GraphQL tester: {e}")

    def run_advanced_fuzzer(self):
        """Run advanced fuzzer"""
        print("\n[*] Running Advanced Fuzzer...")
        print("    Testing: Parameter pollution, encoding, headers, paths")
        print()

        if not self.api_key:
            print("[!] API key required for fuzzer")
            return

        cmd = ['python3', f'{self.script_dir}/fuzzer_advanced.py']

        try:
            user_input = f"{self.api_key}\n"

            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )

            output, _ = process.communicate(input=user_input, timeout=300)
            print(output)

            self.results['tools_run'].append('advanced_fuzzer')

            # Check for findings
            if 'interesting findings' in output.lower() and 'Total interesting findings: 0' not in output:
                print("\n[!!!] FUZZER FOUND SOMETHING!")
                self.results['findings'].append({
                    'tool': 'fuzzer',
                    'note': 'Check fuzzing_results.json'
                })

        except subprocess.TimeoutExpired:
            print("[!] Fuzzer timeout")
        except Exception as e:
            print(f"[!] Error running fuzzer: {e}")

    def run_portal_enumeration(self):
        """Run portal enumeration script"""
        print("\n[*] Running Portal Enumeration...")
        print("    This is interactive - follow the prompts")
        print()

        if not self.api_key:
            print("[!] API key required")
            return

        cmd = ['python3', f'{self.script_dir}/portal_enumeration.py']

        print("[*] Starting interactive portal enumeration...")
        print("[*] Select option 2 to test CTF portal access")
        print()

        try:
            # Run interactively
            subprocess.run(cmd)
            self.results['tools_run'].append('portal_enumeration')
        except Exception as e:
            print(f"[!] Error: {e}")

    def generate_final_report(self):
        """Generate final summary report"""
        print("\n")
        print("="*70)
        print("MASTER HUNTER - FINAL REPORT")
        print("="*70)

        self.results['completed'] = datetime.now().isoformat()

        print(f"\nTools Run: {len(self.results['tools_run'])}")
        for tool in self.results['tools_run']:
            print(f"   {tool}")

        if self.results['findings']:
            print(f"\n TOTAL INTERESTING FINDINGS: {len(self.results['findings'])}")
            for i, finding in enumerate(self.results['findings'], 1):
                print(f"\n[{i}] {finding['tool']}")
                print(f"    {finding['note']}")
        else:
            print("\n[-] No immediate findings across all tools")
            print("    Check individual result files for details")

        # Save summary
        summary_file = '/home/user/Hub/findings/master_hunter_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\nSummary saved to: {summary_file}")

        # Next steps
        print("\n" + "="*70)
        print("NEXT STEPS")
        print("="*70)
        print("""
1. Review all findings files:
   - findings/scan_results_*.json
   - findings/fuzzing_results.json
   - findings/master_hunter_summary.json

2. Check Burp Suite requests:
   - Import requests from burp-requests/ directory
   - Test manually with Burp Repeater
   - Use Burp Intruder for variations

3. Manual testing priorities:
   - Review any non-403 responses carefully
   - Test during different times of day
   - Try race conditions with Turbo Intruder
   - Analyze error messages for data leakage

4. If you found the flag:
   - Extract firstname, super_secret, email values
   - Email submission to the address in email property
   - Subject: "HubSpot CTF Challenge"
   - Include detailed reproduction steps

Good hunting! The flag is out there. 
        """)

    def run_all(self):
        """Run all tools in sequence"""
        self.banner()

        print("[*] Master Hunter will run all automated tools")
        print("[*] This may take 10-15 minutes")
        print()

        # Run automated tools
        self.run_automated_scanner()
        self.run_graphql_tester()
        self.run_advanced_fuzzer()

        # Generate report
        self.generate_final_report()

    def interactive_menu(self):
        """Interactive menu for selective testing"""
        self.banner()

        while True:
            print("\n" + "="*70)
            print("SELECT TOOL TO RUN")
            print("="*70)
            print("1. Full Automated Scan (all tools)")
            print("2. Automated Scanner (direct, batch, search, pollution)")
            print("3. GraphQL Introspection & Testing")
            print("4. Advanced Fuzzer (parameters, headers, encoding)")
            print("5. Portal Enumeration (interactive)")
            print("6. Exit")
            print("="*70)

            choice = input("\nEnter choice (1-6): ").strip()

            if choice == '1':
                self.run_all()
                break
            elif choice == '2':
                self.run_automated_scanner()
            elif choice == '3':
                self.run_graphql_tester()
            elif choice == '4':
                self.run_advanced_fuzzer()
            elif choice == '5':
                self.run_portal_enumeration()
            elif choice == '6':
                print("\n[*] Exiting...")
                break
            else:
                print("\n[!] Invalid choice")


def main():
    parser = argparse.ArgumentParser(
        description='HubSpot CTF Master Hunter - $15,000 Bounty Tool'
    )
    parser.add_argument('--api-key', help='HubSpot API key')
    parser.add_argument('--cookies', help='Session cookies from app.hubspot.com')
    parser.add_argument('--auto', action='store_true', help='Run all tools automatically')

    args = parser.parse_args()

    api_key = args.api_key
    cookies = args.cookies

    # Interactive input if not provided
    if not api_key:
        print("HubSpot CTF Master Hunter\n")
        api_key = input("Enter your HubSpot API key: ").strip()

    if not cookies:
        has_cookies = input("Do you have session cookies? (y/n): ").strip().lower()
        if has_cookies == 'y':
            print("\nPaste session cookies (cookie1=value1; cookie2=value2):")
            cookies = input().strip()

    hunter = MasterHunter(api_key, cookies)

    if args.auto:
        hunter.run_all()
    else:
        hunter.interactive_menu()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user")
        sys.exit(0)
