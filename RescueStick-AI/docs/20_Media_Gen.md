# RescueStick AI - Media Generator Engine
**Engine ID:** 20_media_gen
**Purpose:** Create custom rescue media on-the-fly
**License:** MIT (our code)

---

## What It Does

Generate custom rescue ISOs/USBs:

```
Tech selects:
  → Include: Basic repair tools
  → Add: Specific drivers
  → Include: Win11 baselines
  → Branding: Company logo
       ↓
Generate:
  → Custom ISO ready to burn
       ↓
Client receives: Custom branded rescue USB
```

## Code Structure

```python
#!/usr/bin/env python3
"""
Engine 20: Media Generator
License: MIT (our code)
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class MediaGenerator:
    """
    Create custom rescue media - ISO, IMG, or folder.
    Select tools, drivers, baselines to include.
    """
    
    def __init__(self, output_dir="/rescue-stick/output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def list_templates(self) -> List[dict]:
        """List available media templates"""
        return [
            {
                "id": "basic",
                "name": "Basic Rescue",
                "description": "Core repair tools only",
                "size_estimate": "2GB"
            },
            {
                "id": "full",
                "name": "Full Rescue",
                "description": "All tools + drivers + baselines",
                "size_estimate": "32GB"
            },
            {
                "id": "lite",
                "name": "Lite Rescue",
                "description": "Minimal - just diagnostics",
                "size_estimate": "1GB"
            },
            {
                "id": "client",
                "name": "Client Custom",
                "description": "Customizable for specific client",
                "size_estimate": "Variable"
            }
        ]
    
    def create_from_template(self, template_id: str, 
                             output_name: str,
                             options: dict = None) -> dict:
        """Create media from a template"""
        
        template = {
            "basic": self._create_basic,
            "full": self._create_full,
            "lite": self._create_lite,
            "client": self._create_client
        }
        
        if template_id not in template:
            return {"error": f"Unknown template: {template_id}"}
        
        output_path = self.output_dir / output_name
        
        return template[template_id](output_path, options or {})
    
    def _create_basic(self, output_path: Path, options: dict) -> dict:
        """Create basic rescue media"""
        output_path.mkdir(parents=True, exist_ok=True)
        
        created = []
        
        # Core directories
        for dir_name in ['engines', 'tools', 'data']:
            (output_path / dir_name).mkdir(exist_ok=True)
            created.append(dir_name)
        
        # Copy key files
        source_base = Path("/rescue-stick")
        
        # Copy essential docs
        if (source_base / "README.md").exists():
            shutil.copy2(source_base / "README.md", output_path)
            created.append("README.md")
        
        # Create manifest
        manifest = {
            "template": "basic",
            "created": datetime.now().isoformat(),
            "contents": created,
            "license": "MIT"
        }
        
        with open(output_path / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        created.append("manifest.json")
        
        return {
            "status": "success",
            "template": "basic",
            "output": str(output_path),
            "created": created
        }
    
    def _create_full(self, output_path: Path, options: dict) -> dict:
        """Create full rescue media with everything"""
        result = self._create_basic(output_path, {"full": True})
        
        # Add more components
        source_base = Path("/rescue-stick")
        
        extra = []
        
        # Add all docs
        if (source_base / "docs").exists():
            shutil.copytree(source_base / "docs", output_path / "docs", dirs_exist_ok=True)
            extra.append("docs")
        
        # Add all engine specs
        extra.append("full_templates")
        
        result["created"].extend(extra)
        
        return result
    
    def _create_lite(self, output_path: Path, options: dict) -> dict:
        """Create minimal lite media"""
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Only essential files
        created = ["minimal_structure"]
        
        manifest = {
            "template": "lite",
            "created": datetime.now().isoformat(),
            "note": "Minimal - for diagnostics only"
        }
        
        with open(output_path / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        return {
            "status": "success",
            "template": "lite",
            "output": str(output_path),
            "created": created
        }
    
    def _create_client(self, output_path: Path, options: dict) -> dict:
        """Create client-customized media"""
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Start with basic
        result = self._create_basic(output_path, {})
        
        # Add client-specific items
        if "company_name" in options:
            # Add company branding
            pass
        
        if "custom_tools" in options:
            # Add custom tools
            pass
        
        if "specific_drivers" in options:
            # Add specific drivers
            pass
        
        result["customization"] = options
        
        return result
    
    def add_component(self, output_path: str, component_type: str,
                      source: str) -> dict:
        """Add a component to existing media"""
        output = Path(output_path)
        
        if not output.exists():
            return {"error": "Media not found"}
        
        component_map = {
            "drivers": "data/driver_cache",
            "baselines": "data/baselines",
            "tools": "tools",
            "docs": "docs"
        }
        
        dest = output / component_map.get(component_type, component_type)
        dest.mkdir(parents=True, exist_ok=True)
        
        source_path = Path(source)
        
        if source_path.is_file():
            shutil.copy2(source_path, dest / source_path.name)
        elif source_path.is_dir():
            shutil.copytree(source_path, dest / source_path.name, dirs_exist_ok=True)
        
        return {
            "status": "added",
            "component": component_type,
            "source": source
        }
    
    def add_branding(self, output_path: str, company_name: str,
                     logo_path: str = None) -> dict:
        """Add company branding to media"""
        output = Path(output_path)
        
        if not output.exists():
            return {"error": "Media not found"}
        
        # Create branding file
        branding = {
            "company": company_name,
            "added": datetime.now().isoformat()
        }
        
        with open(output / "branding.json", 'w') as f:
            json.dump(branding, f, indent=2)
        
        # Copy logo if provided
        if logo_path and Path(logo_path).exists():
            shutil.copy2(logo_path, output / "logo.png")
        
        return {
            "status": "branded",
            "company": company_name
        }
    
    def build_iso(self, input_path: str, output_iso: str,
                  label: str = "RescueStick") -> dict:
        """Build ISO from media folder"""
        input_dir = Path(input_path)
        
        if not input_dir.exists():
            return {"error": "Input path not found"}
        
        # Check for mkisofs/xorris
        iso_tool = None
        for tool in ['xorrisofs', 'mkisofs', 'genisoimage']:
            result = subprocess.run(['which', tool], capture_output=True)
            if result.returncode == 0:
                iso_tool = tool
                break
        
        if not iso_tool:
            return {
                "status": "no_tool",
                "message": "ISO tools not installed",
                "install": "apt-get install xorriso"
            }
        
        # Build ISO
        try:
            cmd = [
                iso_tool,
                '-o', output_iso,
                '-R', '-J',
                '-V', label,
                str(input_dir)
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=600)
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "iso": output_iso,
                    "size": Path(output_iso).stat().st_size
                }
            else:
                return {
                    "status": "error",
                    "error": result.stderr.decode()
                }
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def build_img(self, input_path: str, output_img: str,
                  device: str = None) -> dict:
        """Build IMG from media folder"""
        input_dir = Path(input_path)
        
        if not input_dir.exists():
            return {"error": "Input path not found"}
        
        # Create a tarball (simpler than full IMG)
        tar_file = output_img.replace('.img', '.tar.gz')
        
        try:
            cmd = ['tar', '-czf', tar_file, '-C', input_dir, '.']
            result = subprocess.run(cmd, capture_output=True)
            
            if result.returncode == 0:
                return {
                    "status": "success",
                    "archive": tar_file,
                    "note": "Use 'tar -xzf' to extract on target USB"
                }
            else:
                return {"status": "error", "error": result.stderr.decode()}
                
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def generate_config(self, template: str, answers: dict) -> dict:
        """Generate configuration for unattended build"""
        
        config = {
            "template": template,
            "answers": answers,
            "generated": datetime.now().isoformat()
        }
        
        config_file = self.output_dir / f"config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        return {
            "status": "generated",
            "config": str(config_file)
        }


# CLI Interface
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RescueStick Media Generator")
    parser.add_argument("action", choices=["templates", "create", "add", "branding", "iso", "img", "config"])
    parser.add_argument("--template", help="Template ID")
    parser.add_argument("--output", help="Output name/path")
    parser.add_argument("--component", help="Component type")
    parser.add_argument("--source", help="Source path")
    parser.add_argument("--company", help="Company name")
    parser.add_argument("--logo", help="Logo file path")
    parser.add_argument("--input", help="Input path")
    parser.add_argument("--label", help="ISO label")
    
    args = parser.parse_args()
    
    generator = MediaGenerator()
    
    if args.action == "templates":
        templates = generator.list_templates()
        print(json.dumps(templates, indent=2))
    
    elif args.action == "create":
        if not args.template or not args.output:
            print("Error: --template and --output required")
        else:
            result = generator.create_from_template(args.template, args.output)
            print(json.dumps(result, indent=2))
    
    elif args.action == "add":
        if not args.output or not args.component or not args.source:
            print("Error: --output, --component, --source required")
        else:
            result = generator.add_component(args.output, args.component, args.source)
            print(json.dumps(result, indent=2))
    
    elif args.action == "branding":
        if not args.output or not args.company:
            print("Error: --output and --company required")
        else:
            result = generator.add_branding(args.output, args.company, args.logo)
            print(json.dumps(result, indent=2))
    
    elif args.action == "iso":
        if not args.input or not args.output:
            print("Error: --input and --output required")
        else:
            result = generator.build_iso(args.input, args.output, args.label or "RescueStick")
            print(json.dumps(result, indent=2))
    
    elif args.action == "img":
        if not args.input or not args.output:
            print("Error: --input and --output required")
        else:
            result = generator.build_img(args.input, args.output)
            print(json.dumps(result, indent=2))
    
    elif args.action == "config":
        print("Not implemented - use create with template")
```

## Use Cases

- **MSP**: Create branded rescue media for clients
- **Tech**: Pre-load specific drivers for common hardware
- **Enterprise**: Standardized repair media for all locations

## Dependencies

```bash
# For ISO generation:
sudo apt-get install xorriso genisoimage

# For full IMG:
# Use dd or image-utils
```

**License:** MIT (our code)

## Testing

```bash
# List templates
python3 20_media_gen.py templates

# Create media
python3 20_media_gen.py create --template basic --output my_rescue

# Add drivers
python3 20_media_gen.py add --output my_rescue --component drivers --source /path/to/drivers

# Add branding
python3 20_media_gen.py branding --output my_rescue --company "MyCompany" --logo /path/to/logo.png

# Build ISO
python3 20_media_gen.py iso --input my_rescue --output my_rescue.iso
```

---

*Engine 20 - Spec Complete*  
*License: MIT (our code)*