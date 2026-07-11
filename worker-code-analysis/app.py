import boto3
import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor
from enum import Enum
from typing import Any, Optional
import xml.etree.ElementTree as ET

MOCK_BUCKET   = "%VOL-MOUNT%"
WORKSPACE_DIR = os.path.abspath(os.path.dirname(__file__))
TOOLS_DIR     = os.getenv("TOOLS_ROOT", os.path.join(WORKSPACE_DIR, "tools"))
REPORT_DIR    = os.getenv("REPORT_ROOT", os.getenv("REPORT_ROOT", os.path.join(WORKSPACE_DIR, "report")))
SOURCE_DIR    = os.getenv("SOURCES_ROOT", os.getenv("SOURCE_ROOT", os.path.join(WORKSPACE_DIR, "source")))
BUILD_DIR     = os.getenv("BUILD_ROOT", os.getenv("BUILD_ROOT", os.path.join(WORKSPACE_DIR, "build")))

# =====================================================================
# Enums
# =====================================================================

class Type(Enum):
    BUG             = "bug"
    SECURITY        = "security"
    PERFORMANCE     = "performance"
    STYLE           = "style"
    MAINTAINABILITY = "maintainability"
    DOCUMENTATION   = "documentation"
    CONCURRENCY     = "concurrency"


class Urgency(Enum):
    HIGH    = "high"
    MEDIUM  = "medium"
    LOW     = "low"


# =====================================================================
# Mappings
# =====================================================================

MAP_CHECKSTYLE_SEVERITY_TO_URGENCY = {
    "error"   : "high",
    "warning" : "medium",
    "info"    : "low",
    "ignore"  : "low"
}

MAP_CHECKSTYLE_KEYWORD_TO_TYPE = {
    "Javadoc"     : "documentation",
    "Indentation" : "style",
    "Whitespace"  : "style",
    "LineLength"  : "style",
    "Regexp"      : "style",
    "Naming"      : "style",
    "Import"      : "maintainability"
}

MAP_PMD_PRIORITY_TO_URGENCY = {
    "1": "high",
    "2": "high",
    "3": "medium",
    "4": "low",
    "5": "low"
}

MAP_PMD_RULESET_TO_TYPE = {
    "Security"       : "security",
    "Performance"    : "performance",
    "Code Style"     : "style",
    "Error Prone"    : "bug",
    "Design"         : "maintainability",
    "Best Practices" : "maintainability"
}

MAP_PMD_RULE_TO_TYPE = {
    "NoPackage"             : "style",
    "UseUtilityClass"       : "maintainability",
    "ExcessiveMethodLength" : "maintainability",
    "CognitiveComplexity"   : "maintainability"
}

MAP_SPOTBUGS_PRIORITY_TO_URGENCY = {
    "1": "high",
    "2": "medium",
    "3": "low"
}

MAP_SPOTBUGS_CATEGORY_TO_TYPE = {
    "CORRECTNESS"    : "bug",
    "SECURITY"       : "security",
    "PERFORMANCE"    : "performance",
    "STYLE"          : "style",
    "BAD_PRACTICE"   : "maintainability",
    "MT_CORRECTNESS" : "concurrency"
}

_SPOTBUGS_BUG_PATTERN_MAPPING = {
    "NP_ALWAYS_NULL"       : "Possible null pointer dereference",
    "NP_NULL_ON_SOME_PATH" : "Possible null pointer dereference on some execution paths",
    "DLS_DEAD_LOCAL_STORE" : "Value assigned to local variable is never used",
    "URF_UNREAD_FIELD"     : "Field is declared but never read",
    "EI_EXPOSE_REP"        : "Internal mutable state is exposed",
    "EI_EXPOSE_REP2"       : "Internal mutable state is exposed by storing external representation"
}


# =====================================================================
# Helper Path & SpotBugs Message Formatting Functions
# =====================================================================

def _get_relative_source_path(source_path: str, source_root: str = None) -> str:
    """
    Resolves a source path relative to the source_root directory if it is absolute
    and exists on the filesystem.
    """
    if source_root and os.path.isabs(source_path) and os.path.exists(source_path):
        return os.path.relpath(source_path, source_root)
    return source_path


def _find_spotbugs_primary_source_line(bug_instance: ET.Element) -> Optional[ET.Element]:
    """
    Locates the primary SourceLine element inside a BugInstance.
    """
    # 1. Direct children of BugInstance
    direct_sls = [
        child for child in bug_instance
        if child.tag.split("}")[-1] == "SourceLine"
    ]
    if direct_sls:
        for sl in direct_sls:
            if sl.attrib.get("primary") == "true":
                return sl
        return direct_sls[0]

    # 2. Inside Method elements
    methods = [
        child for child in bug_instance
        if child.tag.split("}")[-1] == "Method"
    ]
    for method in methods:
        method_sls = [
            child for child in method
            if child.tag.split("}")[-1] == "SourceLine"
        ]
        if method_sls:
            for sl in method_sls:
                if sl.attrib.get("primary") == "true":
                    return sl
            return method_sls[0]

    # 3. Inside Class elements
    classes = [
        child for child in bug_instance
        if child.tag.split("}")[-1] == "Class"
    ]
    for cls in classes:
        cls_sls = [
            child for child in cls
            if child.tag.split("}")[-1] == "SourceLine"
        ]
        if cls_sls:
            for sl in cls_sls:
                if sl.attrib.get("primary") == "true":
                    return sl
            return cls_sls[0]

    # 4. Fallback: Traverse the entire bug instance structure
    all_sls = []
    for child in bug_instance.iter():
        if child.tag.split("}")[-1] == "SourceLine":
            all_sls.append(child)
    if all_sls:
        for sl in all_sls:
            if sl.attrib.get("primary") == "true":
                return sl
        return all_sls[0]

    return None


def _format_spotbugs_bug_pattern(pattern: str) -> str:
    """
    Formats a bug pattern identifier to a human-readable description.
    """
    if not pattern:
        return "SpotBugs violation"

    if pattern in _SPOTBUGS_BUG_PATTERN_MAPPING:
        return _SPOTBUGS_BUG_PATTERN_MAPPING[pattern]

    parts = pattern.split("_")
    if len(parts) > 1 and parts[0].isupper() and len(parts[0]) <= 4:
        parts = parts[1:]

    message = " ".join(parts).lower()
    if message:
        return message.capitalize()

    return pattern


def _generate_spotbugs_message(bug_instance: ET.Element) -> str:
    """
    Generates a human-readable message for the bug instance.
    """
    long_msg = None
    short_msg = None

    for child in bug_instance:
        tag_local = child.tag.split("}")[-1]
        if tag_local == "LongMessage":
            long_msg = child.text
        elif tag_local == "ShortMessage":
            short_msg = child.text

    if long_msg and long_msg.strip():
        return " ".join(long_msg.strip().split())
    if short_msg and short_msg.strip():
        return " ".join(short_msg.strip().split())

    bug_pattern = bug_instance.attrib.get("type", "")
    return _format_spotbugs_bug_pattern(bug_pattern)


# =====================================================================
# XML Report Normalizer Functions
# =====================================================================

def normalize_checkstyle_report_xml(report_path: str, source_root: str = None) -> dict[str, list[dict]]:
    """
    Normalizes a Checkstyle XML report file into a unified dictionary structure.

    Args:
        report_path (str): Path to the Checkstyle XML report.
        source_root (str, optional): Root directory of the source code to resolve relative paths.

    Returns:
        dict[str, list[dict]]: A dictionary mapping relative Java file paths
            to a list of normalized issue dictionaries.
    """
    normalized_report: dict[str, list[dict]] = {}

    # 1. Check if the report file exists at report_path. If not, return an empty dictionary.
    if not os.path.exists(report_path):
        return normalized_report

    # 2. Parse the XML report using xml.etree.ElementTree. If a ParseError occurs, return an empty dictionary.
    try:
        tree = ET.parse(report_path)
        root = tree.getroot()
    except ET.ParseError:
        return normalized_report

    # 3. Iterate through all elements in the XML tree to locate file elements.
    for elem in root.iter():
        tag_local = elem.tag.split("}")[-1]
        if tag_local != "file":
            continue

        # 4. Extract the name attribute from each file element, which holds the file's path.
        xml_file_path = elem.attrib.get("name")
        if not xml_file_path:
            continue

        # 5. Convert the file path to a relative path using source_root if applicable.
        resolved_path = _get_relative_source_path(xml_file_path, source_root)
        issues: list[dict] = []

        # 6. Iterate through all child elements of the file element to locate error elements.
        for child in elem:
            child_local = child.tag.split("}")[-1]
            if child_local != "error":
                continue

            # 7. For each error element:
            # 7a. Parse the line attribute, defaulting to 1 if it is missing or invalid.
            try:
                line = int(child.attrib.get("line", 1))
            except (ValueError, TypeError):
                line = 1

            # 7b. Parse the column attribute, defaulting to 1 if it is missing or invalid.
            try:
                column = int(child.attrib.get("column", 1))
            except (ValueError, TypeError):
                column = 1

            # 7c. Extract the message attribute, defaulting to "Checkstyle violation" if it is empty.
            message = child.attrib.get("message", "").strip()
            if not message:
                message = "Checkstyle violation"

            # 7d. Extract the severity attribute and map it to an urgency level ('high', 'medium', or 'low').
            severity = child.attrib.get("severity", "").lower()
            urgency_str = MAP_CHECKSTYLE_SEVERITY_TO_URGENCY.get(severity, "medium")
            urgency = Urgency(urgency_str)

            # 7e. Extract the source attribute (the rule/check class) and map it to an issue type ('documentation', 'style', 'maintainability', etc.).
            issue_type = Type.STYLE
            source = child.attrib.get("source", "")
            if source:
                for keyword, t_val in MAP_CHECKSTYLE_KEYWORD_TO_TYPE.items():
                    if keyword in source:
                        issue_type = Type(t_val)
                        break

            issues.append({
                "type": issue_type.value,
                "urgency": urgency.value,
                "line": line,
                "column": column,
                "message": message
            })

        # 8. Collect the parsed issues and group them by the resolved file path.
        if issues:
            normalized_report[resolved_path] = issues

    # 9. Return the dictionary containing all normalized issues.
    return normalized_report


def normalize_pmd_report_xml(report_path: str, source_root: str = None) -> dict[str, list[dict]]:
    """
    Normalizes a PMD XML report file into a unified dictionary structure.

    Args:
        report_path (str): Path to the PMD XML report.
        source_root (str, optional): Root directory of the source code to resolve relative paths.

    Returns:
        dict[str, list[dict]]: A dictionary mapping relative Java file paths
            to a list of normalized issue dictionaries.
    """
    normalized_report: dict[str, list[dict]] = {}

    # 1. Check if the report file exists at report_path. If not, return an empty dictionary.
    if not os.path.exists(report_path):
        return normalized_report

    # 2. Parse the XML report using xml.etree.ElementTree. If a ParseError occurs, return an empty dictionary.
    try:
        tree = ET.parse(report_path)
        root = tree.getroot()
    except ET.ParseError:
        return normalized_report

    # 3. Iterate through all elements in the XML tree to locate file elements.
    for elem in root.iter():
        tag_local = elem.tag.split("}")[-1]
        if tag_local != "file":
            continue

        # 4. Extract the name attribute from each file element, which represents the analyzed file.
        xml_file_path = elem.attrib.get("name")
        if not xml_file_path:
            continue

        # 5. Resolve the file path to a relative path using source_root.
        resolved_path = _get_relative_source_path(xml_file_path, source_root)
        issues: list[dict] = []

        # 6. Iterate through all child elements of the file element to find violation elements.
        for child in elem:
            child_local = child.tag.split("}")[-1]
            if child_local != "violation":
                continue

            # 7. For each violation element:
            # 7a. Parse the beginline attribute, defaulting to 1 if missing or invalid.
            try:
                line = int(child.attrib.get("beginline", 1))
            except (ValueError, TypeError):
                line = 1

            # 7b. Parse the begincolumn attribute, defaulting to 1 if missing or invalid.
            try:
                column = int(child.attrib.get("begincolumn", 1))
            except (ValueError, TypeError):
                column = 1

            # 7c. Extract and clean the text content of the element as the message (collapsing whitespace, defaulting to "PMD violation" if empty).
            raw_message = child.text if child.text else ""
            message = " ".join(raw_message.split())
            if not message:
                message = "PMD violation"

            # 7d. Map the priority attribute (value 1-5) to an urgency level ('high', 'medium', or 'low').
            priority_str = child.attrib.get("priority", "")
            urgency_str = MAP_PMD_PRIORITY_TO_URGENCY.get(priority_str, "medium")
            urgency = Urgency(urgency_str)

            # 7e. Map the ruleset and rule attributes to an issue type ('security', 'performance', 'style', 'bug', 'maintainability').
            ruleset = child.attrib.get("ruleset", "")
            rule = child.attrib.get("rule", "")
            type_str = "maintainability"
            if ruleset and ruleset in MAP_PMD_RULESET_TO_TYPE:
                type_str = MAP_PMD_RULESET_TO_TYPE[ruleset]
            elif rule and rule in MAP_PMD_RULE_TO_TYPE:
                type_str = MAP_PMD_RULE_TO_TYPE[rule]
            issue_type = Type(type_str)

            issues.append({
                "type": issue_type.value,
                "urgency": urgency.value,
                "line": line,
                "column": column,
                "message": message
            })

        # 8. Group and append the parsed issues under the resolved file path.
        if issues:
            normalized_report[resolved_path] = issues

    # 9. Return the resulting normalized report dictionary.
    return normalized_report


def normalize_spotbugs_report_xml(report_path: str, source_root: str = None) -> dict[str, list[dict]]:
    """
    Normalizes a SpotBugs XML report file into a unified dictionary structure.

    Args:
        report_path (str): Path to the SpotBugs XML report.
        source_root (str, optional): Root directory of the source code to resolve relative paths.

    Returns:
        dict[str, list[dict]]: A dictionary mapping relative Java file paths
            to a list of normalized issue dictionaries.
    """
    normalized_report: dict[str, list[dict]] = {}

    # 1. Check if the report file exists at report_path. If not, return an empty dictionary.
    if not os.path.exists(report_path):
        return normalized_report

    # 2. Parse the XML report using xml.etree.ElementTree. If a ParseError occurs, return an empty dictionary.
    try:
        tree = ET.parse(report_path)
        root = tree.getroot()
    except ET.ParseError:
        return normalized_report

    # 3. Iterate through all elements in the XML tree to locate BugInstance elements.
    for elem in root.iter():
        tag_local = elem.tag.split("}")[-1]
        if tag_local != "BugInstance":
            continue

        # 4. For each BugInstance element:
        # 4a. Locate the primary source line using _find_spotbugs_primary_source_line.
        source_line = _find_spotbugs_primary_source_line(elem)

        # 4b. If no primary source line is found, skip this bug instance.
        if source_line is None:
            continue

        # 4c. Extract the source file path from the sourcepath or sourcefile attribute of the source line.
        xml_file_path = source_line.attrib.get("sourcepath")
        if not xml_file_path:
            xml_file_path = source_line.attrib.get("sourcefile")

        if not xml_file_path:
            continue

        # 4d. Resolve the file path to a relative path using source_root.
        resolved_path = _get_relative_source_path(xml_file_path, source_root)

        # 4e. Parse the start line number, defaulting to 1 if missing or invalid. The column number defaults to 1.
        try:
            line = int(source_line.attrib.get("start", 1))
        except (ValueError, TypeError):
            line = 1

        column = 1

        # 4f. Generate a human-readable message using _generate_spotbugs_message.
        message = _generate_spotbugs_message(elem)

        # 4g. Map the priority attribute to an urgency level ('high', 'medium', or 'low').
        priority_str = elem.attrib.get("priority", "")
        urgency_str = MAP_SPOTBUGS_PRIORITY_TO_URGENCY.get(priority_str, "medium")
        urgency = Urgency(urgency_str)

        # 4h. Map the category attribute to an issue type ('bug', 'security', 'performance', 'style', 'maintainability', 'concurrency').
        category = elem.attrib.get("category", "")
        type_str = MAP_SPOTBUGS_CATEGORY_TO_TYPE.get(category, "bug")
        issue_type = Type(type_str)

        issue = {
            "type": issue_type.value,
            "urgency": urgency.value,
            "line": line,
            "column": column,
            "message": message
        }

        # 5. Collect and group all parsed issues by the resolved file path.
        if resolved_path not in normalized_report:
            normalized_report[resolved_path] = []
        normalized_report[resolved_path].append(issue)

    # 6. Return the dictionary of normalized issues.
    return normalized_report


# =====================================================================
# Main Tool Runner Logic
# =====================================================================

def download_from_s3(s3_key: str, dest_dir: str, bucket: str) -> str:
    """
    Downloads a single file from S3 using the provided key and bucket,
    saving it in dest_dir with its filename.
    """
    filename = os.path.basename(s3_key)
    dest_path = os.path.join(dest_dir, filename)

    s3 = boto3.client("s3")
    s3.download_file(bucket, s3_key, dest_path)
    return dest_path


def upload_to_s3(local_file_path: str, s3_key: str, bucket: str) -> None:
    """
    Uploads a single file to S3 using the provided key and bucket.
    """

    s3 = boto3.client("s3")
    s3.upload_file(local_file_path, bucket, s3_key)


def run_checkstyle(source: str, report_dir: str) -> dict:
    CHECKSTYLE_JAR = os.path.join(TOOLS_DIR, "checkstyle", "checkstyle.jar")
    CHECKSTYLE_REPORT_XML = os.path.join(report_dir, "checkstyle.report.xml")

    if os.path.exists(CHECKSTYLE_REPORT_XML):
        os.remove(CHECKSTYLE_REPORT_XML)

    result = subprocess.run(
        args=[
            "java", "-jar",
            CHECKSTYLE_JAR, "-c", "/google_checks.xml", "-f", "xml", "-o", CHECKSTYLE_REPORT_XML, source,
        ],
        cwd=WORKSPACE_DIR,
        capture_output=True
    )

    if result.returncode == 0:
        issues = normalize_checkstyle_report_xml(CHECKSTYLE_REPORT_XML, SOURCE_DIR)
        return {
            "success": True,
            "issues": issues
        }

    return {
        "success": False,
        "errors": result.stderr
    }


def run_pmd(source: str, report_dir: str) -> dict:
    PMD = os.path.join(TOOLS_DIR, "pmd", "bin", "pmd")
    PMD_REPORT_XML = os.path.join(report_dir, "pmd.report.xml")

    if os.path.exists(PMD_REPORT_XML):
        os.remove(PMD_REPORT_XML)

    result = subprocess.run(
        args=[
            PMD, "check",
            "--no-progress",
            "--minimum-priority=MEDIUM",
            "--force-language=java",
            "-f", "xml",
            "-R", "rulesets/java/quickstart.xml",
            "-r", PMD_REPORT_XML,
            "-d", source
        ],
        cwd=WORKSPACE_DIR,
        capture_output=True
    )

    if result.returncode == 0:
        issues = normalize_pmd_report_xml(PMD_REPORT_XML, SOURCE_DIR)
        return {
            "success": True,
            "issues": issues
        }

    return {
        "success": False,
        "errors": result.stderr
    }


def run_spotbugs(source: str, report_dir: str, build_dir: str)-> dict:
    SPOTBUGS = os.path.join(TOOLS_DIR, "spotbugs", "bin", "spotbugs")
    SPOTBUGS_REPORT_XML = os.path.join(report_dir, "spotbugs.report.xml")
    relative_report_xml = os.path.relpath(SPOTBUGS_REPORT_XML, WORKSPACE_DIR)
    relative_build_dir = os.path.relpath(build_dir, WORKSPACE_DIR)

    if os.path.exists(SPOTBUGS_REPORT_XML):
        os.remove(SPOTBUGS_REPORT_XML)

    javac_result = subprocess.run(
        args=[
            "javac", "-d", BUILD_DIR, source
        ]
    )

    if javac_result.returncode != 0:
        return {
            "success": False,
            "errors": javac_result.stderr
        }

    spotbugs_result = subprocess.run(
        args=[
            SPOTBUGS, "-textui", "-xml", "-output", relative_report_xml, relative_build_dir
        ],
        cwd=WORKSPACE_DIR,
        capture_output=True,
    )

    if spotbugs_result.returncode == 0:
        issues = normalize_spotbugs_report_xml(SPOTBUGS_REPORT_XML, SOURCE_DIR)
        return {
            "success": True,
            "issues": issues
        }

    return {
        "success": False,
        "errors": spotbugs_result.stderr
    }

# =====================================================================
# Handler function for AWS Lambda
# =====================================================================

def lambda_handler(event: Any, context: Any) -> dict:
    # Parse event if it is a JSON string

    if not event or not isinstance(event, dict):
        return {
            "statusCode": 400,
            "body": {
                "error": "empty event"
            }
        }
    
    if "job_id" not in event:
        return {
            "statusCode": 400,
            "body": {
                "error": "missing job_id"
            }
        }
    
    if "source_key" not in event:
        return {
            "statusCode": 400,
            "body": {
                "error": "missing source_key"
            }
        }

    if "report_key" not in event:
        return {
            "statusCode": 400,
            "body": {
                "error": "missing report_key"
            }
        }

    bucket = os.getenv("AWS_S3_BUCKET")
    if not bucket:
        return {
            "statusCode": 500,
            "body": {
                "error": "AWS_S3_BUCKET not set"
            }
        }

    job_id = event["job_id"]
    source_key = event["source_key"]
    report_key = event["report_key"]
    is_mock_bucket = bucket == MOCK_BUCKET
    source_dir = SOURCE_DIR if is_mock_bucket else os.path.join(SOURCE_DIR, job_id)
    report_dir = REPORT_DIR if is_mock_bucket else os.path.join(REPORT_DIR, job_id)
    build_dir = BUILD_DIR if is_mock_bucket else os.path.join(BUILD_DIR, job_id)
    combined_report: dict[str, list[dict]] = {}
    report_file_path = os.path.join(report_dir, "report.json")

    os.makedirs(source_dir, exist_ok=True)
    os.makedirs(report_dir, exist_ok=True)
    os.makedirs(build_dir, exist_ok=True)

    if not is_mock_bucket:
        try:
            source = download_from_s3(source_key, source_dir, bucket)
        except Exception as e:
            print(e)
            return {
                "statusCode": 500,
                "body": {
                    "error": "fail to download source code"
                }
            }
    else:
        source = None
        for item in os.listdir(SOURCE_DIR):
            item_path = os.path.join(SOURCE_DIR, item)
            if os.path.isfile(item_path) and item.endswith(".java"):
                source = item_path
                break
        

    if not source or not os.path.isfile(source):
        return {
            "statusCode": 400,
            "body": {
                "error": "No Java source code found for analysis."
            }
        }

    with ThreadPoolExecutor(max_workers=3) as pool:
        cs_future  = pool.submit(run_checkstyle, source, report_dir)
        pmd_future = pool.submit(run_pmd, source, report_dir)
        sb_future  = pool.submit(run_spotbugs, source, report_dir, build_dir)

        cs_report  = cs_future.result()
        pmd_report = pmd_future.result()
        sb_report  = sb_future.result()


    for report in [cs_report, pmd_report, sb_report]:
        if report["success"]:
            issues: dict[str, list[dict]] = report["issues"]
            for k, v in issues.items():
                if k not in combined_report:
                    combined_report[k] = []
                combined_report[k].extend(v)

    
    with open(report_file_path, "w", encoding="utf-8") as f:
        json.dump(combined_report, f)

    if not is_mock_bucket:
        try:
            upload_to_s3(report_file_path, report_key, bucket)
        except Exception as e:
            return {
                "statusCode": 500,
                "body": {
                    "error": "fail to upload report"
                }
            }

    return {
        "statusCode": 200,
        "body": {
            "message": "Analysis completed successfully",
            "job_id": job_id
        }
    }
