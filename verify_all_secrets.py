#!/usr/bin/env python3
"""
Complete GSM Secrets Verification Script
Checks all 23 production secrets and their values
"""

import subprocess
import sys


def check_secret(secret_name, show_value=False, mask_length=8):
    """Check if a secret exists and optionally show its value"""
    try:
        result = subprocess.run(
            [
                r"C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
                "secrets",
                "versions",
                "access",
                "latest",
                f"--secret={secret_name}",
                "--project=my-hibachi-crm",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode == 0:
            value = result.stdout.strip()
            if show_value:
                if len(value) > mask_length:
                    masked_value = (
                        value[:mask_length] + "..." + f"({len(value)} chars)"
                    )
                else:
                    masked_value = value
                return True, masked_value
            else:
                return True, f"✅ EXISTS ({len(value)} chars)"
        else:
            return False, f"❌ ERROR: {result.stderr.strip()}"
    except Exception as e:
        return False, f"❌ FAILED: {e!s}"


def main():
    print("🔍 COMPLETE GSM SECRETS VERIFICATION")
    print("=" * 60)

    # Define all expected secrets by category
    secrets = {
        "🌍 GLOBAL SECRETS": [
            "prod-global-CONFIG_VERSION",
            "prod-global-STRIPE_SECRET_KEY",
            "prod-global-OPENAI_API_KEY",
            "prod-global-GOOGLE_MAPS_SERVER_KEY",
        ],
        "🖥️ BACKEND API SECRETS": [
            "prod-backend-api-JWT_SECRET",
            "prod-backend-api-ENCRYPTION_KEY",
            "prod-backend-api-DB_URL",
            "prod-backend-api-REDIS_URL",
            "prod-backend-api-RC_CLIENT_ID",
            "prod-backend-api-RC_CLIENT_SECRET",
            "prod-backend-api-DEEPGRAM_API_KEY",
            "prod-backend-api-SMTP_PASSWORD",
            "prod-backend-api-GMAIL_APP_PASSWORD",
        ],
        "🌐 FRONTEND WEB SECRETS": [
            "prod-frontend-web-NEXT_PUBLIC_API_URL",
            "prod-frontend-web-NEXT_PUBLIC_APP_URL",
            "prod-frontend-web-NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY",
            "prod-frontend-web-NEXT_PUBLIC_GOOGLE_MAPS_API_KEY",
            "prod-frontend-web-NEXT_PUBLIC_BUSINESS_PHONE",
            "prod-frontend-web-NEXT_PUBLIC_BUSINESS_EMAIL",
            "prod-frontend-web-NEXT_PUBLIC_ZELLE_EMAIL",
        ],
        "👨‍💼 FRONTEND ADMIN SECRETS": [
            "prod-frontend-admin-NEXT_PUBLIC_API_URL",
            "prod-frontend-admin-NEXT_PUBLIC_APP_URL",
            "prod-frontend-admin-NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY",
        ],
    }

    total_secrets = 0
    working_secrets = 0
    failed_secrets = []

    for category, secret_list in secrets.items():
        print(f"\n{category}")
        print("-" * 50)

        for secret in secret_list:
            total_secrets += 1
            # Show values for some critical secrets
            show_value = secret in [
                "prod-global-CONFIG_VERSION",
                "prod-frontend-web-NEXT_PUBLIC_BUSINESS_PHONE",
                "prod-frontend-web-NEXT_PUBLIC_BUSINESS_EMAIL",
            ]

            success, message = check_secret(secret, show_value=show_value)
            short_name = (
                secret.replace("prod-", "")
                .replace("frontend-", "")
                .replace("backend-", "")
            )

            if success:
                working_secrets += 1
                print(f"  ✅ {short_name}: {message}")
            else:
                failed_secrets.append(secret)
                print(f"  ❌ {short_name}: {message}")

    print("\n" + "=" * 60)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 60)
    print(f"✅ Working Secrets: {working_secrets}/{total_secrets}")
    print(f"❌ Failed Secrets: {len(failed_secrets)}")

    if failed_secrets:
        print("\n🚨 Failed Secrets:")
        for secret in failed_secrets:
            print(f"  - {secret}")
        print("\n❌ VERIFICATION FAILED")
        return False
    else:
        print(f"\n🎉 ALL {total_secrets} SECRETS VERIFIED SUCCESSFULLY!")
        print("🔐 Enterprise Secret Management: FULLY OPERATIONAL")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
