import json
import os
import glob
import pprint
import subprocess
import sys

esrp_tool = os.path.join("esrp", "tools", "EsrpClient.exe")

AAD_ID  = "38aa33bc-a7e7-4007-bfb2-e8b17f04aadc"
WORKSPACE = os.environ['GITHUB_WORKSPACE'].strip()
ARTIFACTS_DIR = os.environ['ARTIFACTS_DIR'].strip()

def main():
    source_root_location = os.path.join(WORKSPACE, ARTIFACTS_DIR, "unsigned")
    destination_location = os.path.join(WORKSPACE, ARTIFACTS_DIR)

    files = glob.glob(os.path.join(source_root_location, "*.deb"))

    print("Found files:")
    pprint.pp(files)

    if len(files) < 1 or not files[0].endswith(".deb"):
        print("Error: cannot find .deb to sign")
        exit(1)

    file_to_sign = os.path.basename(files[0])

    auth_json = {
        "Version": "1.0.0",
        "AuthenticationType": "AAD_CERT",
        "TenantId": "72f988bf-86f1-41af-91ab-2d7cd011db47",
        "ClientId": AAD_ID,
        "AuthCert": {
            "SubjectName": f"CN={AAD_ID}.microsoft.com",
            "StoreLocation": "LocalMachine",
            "StoreName": "My",
        },
        "RequestSigningCert": {
            "SubjectName": f"CN={AAD_ID}",
            "StoreLocation": "LocalMachine",
            "StoreName": "My",
        }
    }

    input_json = {
        "Version": "1.0.0",
        "SignBatches": [
            {
                "SourceLocationType": "UNC",
                "SourceRootDirectory": source_root_location,
                "DestinationLocationType": "UNC",
                "DestinationRootDirectory": destination_location,
                "SignRequestFiles": [
                    {
                        "CustomerCorrelationId": "01A7F55F-6CDD-4123-B255-77E6F212CDAD",
                        "SourceLocation": file_to_sign,
                        "DestinationLocation": os.path.join("signed", file_to_sign),
                    }
                ],
                "SigningInfo": {
                    "Operations": [
                        {
                            "KeyCode": "CP-450779-Pgp",
                            "OperationCode": "LinuxSign",
                            "Parameters": {},
                            "ToolName": "sign",
                            "ToolVersion": "1.0",
                        }
                    ]
                }
            }
        ]
    }

    policy_json = {
        "Version": "1.0.0",
        "Intent": "production release",
        "ContentType": "Debian package",
    }

    configs = [
        ("auth.json", auth_json),
        ("input.json", input_json),
        ("policy.json", policy_json),
    ]

    for filename, data in configs:
        with open(filename, 'w') as fp:
            json.dump(data, fp)

    # Run ESRP Client
    esrp_out = "esrp_out.json"
    result = subprocess.run(
        [esrp_tool, "sign",
        "-a", "auth.json",
        "-i", "input.json",
        "-p", "policy.json",
        "-o", esrp_out,
        "-l", "Verbose"],
        cwd=WORKSPACE)

    if result.returncode != 0:
        print("Failed to run ESRPClient.exe")
        sys.exit(1)

    if os.path.isfile(esrp_out):
        print("ESRP output json:")
        with open(esrp_out, 'r') as fp:
            pprint.pp(json.load(fp))

    signed_file = os.path.join(destination_location, "signed", file_to_sign)
    if os.path.isfile(signed_file):
        print(f"Success!\nSigned {signed_file}")

if __name__ == "__main__":
    main()