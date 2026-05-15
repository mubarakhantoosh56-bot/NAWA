export type Company = {
  id: string;
  slug: string;
  name: string;
  status: string;
  plan: string;
};

export type User = {
  id: string;
  email: string;
  full_name: string;
  status: string;
  auth_provider: string;
};

export type Membership = {
  id: string;
  company_id: string;
  user_id: string;
  role_id: string;
  department_id: string | null;
  status: string;
};

export type Role = {
  id: string;
  slug: string;
  name: string;
  permissions: string[];
  is_system_role: boolean;
};

export type AuthResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  company: Company;
  user: User;
  membership: Membership;
};

export type MeResponse = {
  company: Company;
  user: User;
  membership: Membership;
  role: Role;
};
