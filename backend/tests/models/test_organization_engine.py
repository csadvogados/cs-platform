from app.models.organization import Organization
from app.models.organization_address import OrganizationAddress
from app.models.organization_branding import OrganizationBranding
from app.models.organization_license import OrganizationLicense
from app.models.organization_settings import OrganizationSettings

def test_tables_are_registered():
    assert Organization.__tablename__ == "organizations"
    assert OrganizationSettings.__tablename__ == "organization_settings"
    assert OrganizationBranding.__tablename__ == "organization_branding"
    assert OrganizationLicense.__tablename__ == "organization_licenses"
    assert OrganizationAddress.__tablename__ == "organization_addresses"
