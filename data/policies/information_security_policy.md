# Information Security Policy

## Scope

This policy protects the confidentiality, integrity, and availability of company and customer data. All employees, contractors, and authorized third parties who access company systems must adhere to these security controls. This policy complements the **Acceptable Use Policy** and **Confidentiality and NDA Policy**; violations of those policies may also constitute security violations. The Chief Information Security Officer (CISO) owns this policy; IT and Security operations enforce it.

## Definitions

- **Confidentiality**: Ensuring that information is accessible only to authorized individuals.
- **Integrity**: Ensuring that information is accurate and has not been altered inappropriately.
- **Availability**: Ensuring that information and systems are accessible when needed.
- **PII (Personally Identifiable Information)**: Data that can identify an individual, such as name, SSN, date of birth, or financial account numbers.
- **MFA (Multi-Factor Authentication)**: Authentication requiring at least two factors (e.g., password plus a code from an app or device).

## Data Classification

| Classification | Examples | Handling Requirements |
|----------------|----------|------------------------|
| **Public** | Marketing materials, press releases, public documentation | No restrictions; may be shared externally |
| **Internal** | Internal memos, process docs, team wikis | Internal systems only; no external sharing without approval |
| **Confidential** | Customer data, financials, contracts, pricing | Encrypted at rest and in transit; access-controlled; audit-logged |
| **Restricted** | PII, trade secrets, health data (e.g., FMLA documentation) | Maximum protection; need-to-know access; audit-logged; special handling per compliance requirements |

- All data must be classified by its owner or creator.
- Downstream data inherits the highest classification of its source components.
- Reclassification requests require approval from the data owner and, for Restricted data, the Security team.

## Access Control

- **Passwords**: Minimum 12 characters; mix of uppercase, lowercase, numbers, and symbols; no reuse across company and personal accounts.
- **MFA**: Required for all company systems; no exceptions. Use an authenticator app or hardware key; SMS may be used as a fallback where supported.
- **Access grants**: Granted on a need-to-know basis. Request access via the IT portal; managers approve; IT provisions.
- **Access reviews**: Managers review direct report access quarterly; IT revokes access for role changes or separation.
- **Offboarding**: Access revoked within 24 hours of separation. HR notifies IT; IT executes revocation.
- **Third-party access**: Requires a signed agreement and Security review. Access is time-limited and scoped.

## Device Security

- Company-issued devices must have full-disk encryption enabled and screen lock after 5 minutes of inactivity.
- Install only approved software from the company app store or through IT. No sideloading or unapproved applications.
- Report lost or stolen devices to IT and Security **immediately**. Remote wipe will be initiated.
- Personal devices may not be used to access or store Confidential or Restricted data unless explicitly approved and configured for secure access (e.g., MDM-managed).
- Use of company devices is subject to the **Acceptable Use Policy**; personal use must not compromise security.

## Email and Communication

- Do not send Confidential or Restricted data via unencrypted email. Use the approved secure file-sharing solution.
- Verify sender identity for requests involving sensitive data or financial transactions; be alert to phishing and business email compromise.
- Report suspected phishing or security incidents to security@company.com immediately. Do not click suspicious links or open unexpected attachments.
- Emails may be monitored for security and compliance; business communications are not private.

## Network and Cloud Security

- Use the company VPN when accessing internal resources from off-network (e.g., home, travel).
- Do not connect to unsecured or unknown Wi-Fi networks when handling Confidential or Restricted data.
- Cloud storage: Use only approved services. Do not sync Confidential or Restricted data to personal cloud accounts.
- Backups are managed by IT; do not create unauthorized copies of sensitive data on removable media or personal devices.

## Incident Response

- **Report**: Any suspected breach, malware, data loss, or security incident must be reported to security@company.com within 24 hours. Reporting is mandatory; good-faith reporters will not be disciplined.
- **Contain**: Follow Security team instructions. Do not attempt unassisted remediation (e.g., wiping a device before approval).
- **Document**: Preserve evidence; note timelines, actions taken, and individuals involved. Do not delete logs or alter systems.
- **Coordinate**: Security will coordinate with IT, Legal, and affected stakeholders as needed.

## Training and Awareness

- Annual security awareness training is mandatory for all employees. Completion is tracked.
- Role-specific training (e.g., SOC2, handling PII, secure development) is required for relevant personnel.
- Non-completion may result in restricted access or disciplinary action.
- Phishing simulations may be conducted; repeated failure may trigger additional training.

## Enforcement

- Violations may result in warning, restricted access, disciplinary action up to termination, and legal action where appropriate.
- Repeat or serious violations will be escalated to HR and Legal.
- Contractors and third parties may have their access revoked and agreements terminated.

## FAQ

**Q: Can I use a password manager?**  
A: Yes, company-approved password managers are encouraged. Do not share master passwords.

**Q: What if I accidentally send sensitive data to the wrong recipient?**  
A: Report immediately to security@company.com. Do not attempt to recall or delete; Security will assess and advise.

**Q: Is it okay to use personal devices for work?**  
A: Only if approved and configured per IT policy. Personal devices may not be used for Confidential or Restricted data without such approval.

**Q: Who do I contact for a lost laptop?**  
A: Contact IT and Security immediately. A ticket will be created and remote wipe initiated.

## Related Policies

- **Acceptable Use Policy**: Governs use of IT resources and prohibited activities.
- **Confidentiality and NDA Policy**: Governs handling of confidential information.
- **Remote Work Policy**: Additional security requirements for remote work environments.

## Contact

Security: security@company.com | IT Helpdesk: helpdesk@company.com | Policy questions: compliance@company.com
