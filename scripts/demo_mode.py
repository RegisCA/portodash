#!/usr/bin/env python3
"""
Toggle between real portfolio data and demo data.

This script safely swaps between your real portfolio data and demo/sample data
for taking screenshots or testing without exposing your real holdings.

Usage:
    python scripts/demo_mode.py          # Toggle mode
    python scripts/demo_mode.py --status # Check current mode

Files managed:
    - portfolio.json
    - historical.csv

Note: fx_rates.csv is not swapped as it contains portfolio-agnostic data.

When switching to demo mode:
    1. Backs up real files as *.real
    2. Copies *.sample files to active names
    3. Creates .demo_mode marker

When switching back to real mode:
    1. Restores *.real files
    2. Removes .demo_mode marker
"""
import argparse
import shutil
import sys
from pathlib import Path


class DemoMode:
    def __init__(self, base_dir=None):
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        self.marker_file = self.base_dir / '.demo_mode'
        
        self.files = {
            'portfolio.json': {
                'active': self.base_dir / 'portfolio.json',
                'sample': self.base_dir / 'portfolio.json.sample',
                'backup': self.base_dir / 'portfolio.json.real',
            },
            'historical.csv': {
                'active': self.base_dir / 'historical.csv',
                'sample': self.base_dir / 'historical.csv.sample',
                'backup': self.base_dir / 'historical.csv.real',
            },
        }
    
    def is_demo_mode(self):
        """Check if currently in demo mode."""
        return self.marker_file.exists()
    
    def get_status(self):
        """Get detailed status of all files."""
        mode = "DEMO" if self.is_demo_mode() else "REAL"
        status = {
            'mode': mode,
            'files': {}
        }
        
        for name, paths in self.files.items():
            status['files'][name] = {
                'active': paths['active'].exists(),
                'sample': paths['sample'].exists(),
                'backup': paths['backup'].exists(),
            }
        
        return status
    
    def print_status(self):
        """Print current status."""
        status = self.get_status()
        
        print(f"📊 Portfolio Dashboard Mode: {status['mode']}")
        print()
        
        if status['mode'] == 'DEMO':
            print("   Using demo/sample data for screenshots and testing")
            print("   Real data is safely backed up as *.real files")
        else:
            print("   Using real portfolio data")
        
        print()
        print("Files:")
        for name, files in status['files'].items():
            active_icon = "✅" if files['active'] else "❌"
            print(f"  {active_icon} {name:20} (active)")
            
            if status['mode'] == 'DEMO':
                backup_icon = "✅" if files['backup'] else "⚠️ "
                print(f"     {backup_icon} {name:20}.real (backup)")
            else:
                sample_icon = "✅" if files['sample'] else "❌"
                print(f"     {sample_icon} {name:20}.sample")
    
    def switch_to_demo(self):
        """Switch from real data to demo data."""
        if self.is_demo_mode():
            print("❌ Already in demo mode!")
            return False
        
        print("🎨 Switching to DEMO mode...")
        print()
        
        # Check sample files exist
        missing_samples = []
        for name, paths in self.files.items():
            if not paths['sample'].exists():
                missing_samples.append(name + '.sample')
        
        if missing_samples:
            print(f"❌ Missing sample files: {', '.join(missing_samples)}")
            print()
            print("Please create sample files first:")
            print("  - portfolio.json.sample (should exist)")
            print("  - historical.csv.sample (run: python scripts/generate_demo_data.py)")
            print("  - fx_rates.csv.sample (should exist)")
            return False
        
        # Backup and swap files
        for name, paths in self.files.items():
            if paths['active'].exists():
                print(f"📦 Backing up {name} → {name}.real")
                shutil.copy2(paths['active'], paths['backup'])
                paths['active'].unlink()
            else:
                print(f"⏭️  Skipping {name} (doesn't exist)")
            
            print(f"📋 Copying {name}.sample → {name}")
            shutil.copy2(paths['sample'], paths['active'])
        
        # Create marker
        self.marker_file.touch()
        
        print()
        print("✅ Switched to demo mode!")
        print()
        print("Your real data is safely backed up as *.real files")
        print("Run this script again to switch back to real data")
        return True
    
    def switch_to_real(self):
        """Switch from demo data back to real data."""
        if not self.is_demo_mode():
            print("❌ Already in real mode!")
            return False
        
        print("🏠 Switching to REAL mode...")
        print()
        
        # Check backup files exist
        missing_backups = []
        for name, paths in self.files.items():
            if not paths['backup'].exists():
                missing_backups.append(name + '.real')
        
        if missing_backups:
            print(f"⚠️  Warning: Missing backup files: {', '.join(missing_backups)}")
            response = input("Continue anyway? [y/N]: ")
            if response.lower() != 'y':
                print("Cancelled.")
                return False
        
        # Restore files
        for name, paths in self.files.items():
            if paths['active'].exists():
                print(f"🗑️  Removing demo {name}")
                paths['active'].unlink()
            
            if paths['backup'].exists():
                print(f"📦 Restoring {name}.real → {name}")
                shutil.copy2(paths['backup'], paths['active'])
                paths['backup'].unlink()
            else:
                print(f"⏭️  No backup for {name}")
        
        # Remove marker
        self.marker_file.unlink()
        
        print()
        print("✅ Switched to real mode!")
        print()
        print("Your real portfolio data is now active")
        return True
    
    def toggle(self):
        """Toggle between demo and real mode."""
        if self.is_demo_mode():
            return self.switch_to_real()
        else:
            return self.switch_to_demo()


def main():
    parser = argparse.ArgumentParser(
        description='Toggle between real and demo portfolio data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/demo_mode.py           # Toggle mode
  python scripts/demo_mode.py --status  # Check current mode

This script safely manages switching between your real portfolio data
and demo/sample data for screenshots and testing.
        """
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show current mode without switching'
    )
    
    args = parser.parse_args()
    
    demo = DemoMode()
    
    if args.status:
        demo.print_status()
    else:
        print("=" * 60)
        demo.print_status()
        print("=" * 60)
        print()
        
        if demo.is_demo_mode():
            response = input("Switch back to REAL data? [y/N]: ")
        else:
            response = input("Switch to DEMO data? [y/N]: ")
        
        if response.lower() == 'y':
            print()
            demo.toggle()
        else:
            print("Cancelled.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
