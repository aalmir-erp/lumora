#!/usr/bin/env python3
"""Copy widget Java + resources from twa/android/widget-sources/ into the
Bubblewrap-generated TWA project at twa/android/generated/. Also injects
the AndroidManifest <receiver> entries.

Usage: inject-widgets.py <generated_dir>"""
import os, re, shutil, sys


def main(gen_dir: str) -> None:
    src = os.path.join(os.environ.get("GITHUB_WORKSPACE", "."),
                       "twa/android/widget-sources")
    if not os.path.isdir(src):
        sys.exit(f"Widget sources missing at {src}")

    # 1) Java files → app/src/main/java/ae/servia/app/
    java_dst = os.path.join(gen_dir, "app/src/main/java/ae/servia/app")
    os.makedirs(java_dst, exist_ok=True)
    for f in os.listdir(os.path.join(src, "java")):
        if f.endswith(".java"):
            shutil.copy(os.path.join(src, "java", f),
                        os.path.join(java_dst, f))
            print(f"  java/{f}")

    # 2) Layouts → res/layout/
    layout_dst = os.path.join(gen_dir, "app/src/main/res/layout")
    os.makedirs(layout_dst, exist_ok=True)
    for f in os.listdir(os.path.join(src, "res-layout")):
        if f.endswith(".xml"):
            shutil.copy(os.path.join(src, "res-layout", f),
                        os.path.join(layout_dst, f))
            print(f"  res/layout/{f}")

    # 3) XML configs → res/xml/
    xml_dst = os.path.join(gen_dir, "app/src/main/res/xml")
    os.makedirs(xml_dst, exist_ok=True)
    for f in os.listdir(os.path.join(src, "res-xml")):
        if f.endswith(".xml"):
            shutil.copy(os.path.join(src, "res-xml", f),
                        os.path.join(xml_dst, f))
            print(f"  res/xml/{f}")

    # 4) Drawables → res/drawable/
    draw_dst = os.path.join(gen_dir, "app/src/main/res/drawable")
    os.makedirs(draw_dst, exist_ok=True)
    for f in os.listdir(os.path.join(src, "res-drawable")):
        if f.endswith(".xml"):
            shutil.copy(os.path.join(src, "res-drawable", f),
                        os.path.join(draw_dst, f))
            print(f"  res/drawable/{f}")

    # 5) Append strings to existing strings.xml (don't blow away bubblewrap's)
    extra_strings_path = os.path.join(src, "res-values/servia_widget_strings.xml")
    main_strings_path = os.path.join(gen_dir, "app/src/main/res/values/strings.xml")
    if os.path.exists(extra_strings_path) and os.path.exists(main_strings_path):
        with open(extra_strings_path) as f:
            extra = f.read()
        # Pull <string ...> entries out
        for m in re.finditer(r'(<string\s+name="[^"]+">[^<]*</string>)', extra):
            tag = m.group(1)
            with open(main_strings_path) as f:
                cur = f.read()
            if tag in cur:
                continue
            # Insert before </resources>
            new = cur.replace("</resources>", f"    {tag}\n</resources>", 1)
            with open(main_strings_path, "w") as f:
                f.write(new)
        print(f"  res/values/strings.xml (appended widget descriptions)")

    # 6) Inject <receiver> tags into AndroidManifest.xml before </application>
    manifest_path = os.path.join(gen_dir, "app/src/main/AndroidManifest.xml")
    with open(manifest_path) as f:
        manifest = f.read()
    receivers_path = os.path.join(src, "manifest-receivers.xml")
    with open(receivers_path) as f:
        receivers = f.read()
    if "QuickBookWidget" not in manifest:
        new_manifest = manifest.replace("</application>",
                                        receivers + "\n    </application>", 1)
        with open(manifest_path, "w") as f:
            f.write(new_manifest)
        print("  AndroidManifest.xml (injected widget receivers)")
    else:
        print("  AndroidManifest.xml (already has widget receivers)")

    print("Widget injection complete.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "twa/android/generated")
