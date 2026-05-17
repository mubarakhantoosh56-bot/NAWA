import { apiRequest } from "@/lib/api/client";
import type { CompanyIntelligenceProfile } from "@/lib/types";

export function getCompanyIntelligenceProfile(token: string): Promise<CompanyIntelligenceProfile> {
  return apiRequest<CompanyIntelligenceProfile>(
    "/company/intelligence-profile",
    { method: "GET" },
    { token },
  );
}

export function updateCompanyIntelligenceProfile(
  token: string,
  profile: CompanyIntelligenceProfile,
): Promise<CompanyIntelligenceProfile> {
  return apiRequest<CompanyIntelligenceProfile>(
    "/company/intelligence-profile",
    { method: "PUT" },
    {
      token,
      body: {
        company_name: profile.company_name,
        industry: profile.industry,
        business_type: profile.business_type,
        country_market: profile.country_market,
        company_size: profile.company_size,
        departments_enabled: profile.departments_enabled,
        primary_goals: profile.primary_goals,
        current_operational_challenges: profile.current_operational_challenges,
        growth_priorities: profile.growth_priorities,
        preferred_response_language: profile.preferred_response_language,
      },
    },
  );
}
