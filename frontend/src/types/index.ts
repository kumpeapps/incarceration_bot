export interface Inmate {
  id: number;
  name: string;
  race: string;
  sex: string;
  cell_block?: string;
  arrest_date?: string;
  held_for_agency?: string;
  mugshot?: string;
  dob: string;
  hold_reasons: string;
  is_juvenile: boolean;
  release_date: string;
  in_custody_date: string;
  jail_id: string;
  hide_record: boolean;
  jail?: Jail;
}

export interface Jail {
  id: number;
  jail_name: string;
  state: string;
  jail_id: string;
  scrape_system: string;
  active: boolean;
  created_date: string;
  updated_date: string;
  last_scrape_date?: string;
  last_successful_scrape?: string;
}

export interface Monitor {
  id: number;
  name: string;
  arrest_date?: string;
  release_date?: string;
  arrest_reason?: string;
  arresting_agency?: string;
  jail?: string;
  mugshot?: string;
  enable_notifications: number;
  notify_method?: string;
  notify_address: string;
  last_seen_incarcerated?: string;
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: 'admin' | 'user';
  created_at: string;
  last_login?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface InmateSearchParams {
  name?: string;
  jail_id?: string;
  race?: string;
  sex?: string;
  is_juvenile?: boolean;
  in_custody?: boolean;
  page?: number;
  limit?: number;
}

export interface MonitorSearchParams {
  name?: string;
  notify_method?: string;
  enable_notifications?: boolean;
  page?: number;
  limit?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  limit: number;
  pages: number;
}

export interface DashboardStats {
  total_inmates: number;
  total_active_inmates: number;
  total_monitors: number;
  total_jails: number;
  active_jails: number;
  recent_arrests: number;
  recent_releases: number;
}
