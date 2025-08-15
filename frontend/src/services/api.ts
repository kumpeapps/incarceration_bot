import axios, { AxiosInstance } from 'axios';
import {
  Inmate,
  Monitor,
  Jail,
  User,
  Group,
  LoginRequest,
  LoginResponse,
  InmateSearchParams,
  MonitorSearchParams,
  PaginatedResponse,
  DashboardStats,
} from '../types';
import { getConfig } from '../config/runtime';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    const config = getConfig();
    this.api = axios.create({
      baseURL: config.API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.api.interceptors.request.use((config) => {
      const token = localStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle token expiration
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('auth_token');
          localStorage.removeItem('user');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Authentication
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.api.post('/auth/login', credentials);
    return response.data;
  }

  async logout(): Promise<void> {
    await this.api.post('/auth/logout');
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
  }

  // Configuration
  async getUserManagementConfig(): Promise<{ external_user_management: boolean; description: string }> {
    const response = await this.api.get('/config/user-management');
    return response.data;
  }

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await this.api.get('/dashboard/stats');
    return response.data;
  }

  // Inmates
  async getInmates(params?: InmateSearchParams): Promise<PaginatedResponse<Inmate>> {
    const response = await this.api.get('/inmates', { params });
    return response.data;
  }

  async getInmate(id: number): Promise<Inmate> {
    const response = await this.api.get(`/inmates/${id}`);
    return response.data;
  }

  async searchInmates(query: string): Promise<Inmate[]> {
    const response = await this.api.get(`/inmates/search`, { 
      params: { q: query } 
    });
    return response.data;
  }

  // Monitors
  async getMonitors(params?: MonitorSearchParams): Promise<PaginatedResponse<Monitor>> {
    const response = await this.api.get('/monitors', { params });
    return response.data;
  }

  async getMonitor(id: number): Promise<Monitor> {
    const response = await this.api.get(`/monitors/${id}`);
    return response.data;
  }

  async createMonitor(monitor: Omit<Monitor, 'id'>): Promise<Monitor> {
    const response = await this.api.post('/monitors', monitor);
    return response.data;
  }

  async updateMonitor(id: number, monitor: Partial<Monitor>): Promise<Monitor> {
    const response = await this.api.put(`/monitors/${id}`, monitor);
    return response.data;
  }

  async deleteMonitor(id: number): Promise<void> {
    await this.api.delete(`/monitors/${id}`);
  }

  // Monitor assignment and linking (Admin functionality)
  async assignMonitor(monitorId: number, userId: number): Promise<{ message: string }> {
    const response = await this.api.put(`/monitors/${monitorId}/assign/${userId}`);
    return response.data;
  }

  async linkMonitors(monitorId: number, linkedMonitorId: number, reason?: string): Promise<{ message: string }> {
    const response = await this.api.post(`/monitors/${monitorId}/link`, {
      linked_monitor_id: linkedMonitorId,
      link_reason: reason,
    });
    return response.data;
  }

  async getMonitorInmateRecord(monitorId: number): Promise<any> {
    const response = await this.api.get(`/monitors/${monitorId}/inmate-record`);
    return response.data;
  }

  // Monitor-Inmate Link Management
  async getMonitorInmateLinks(monitorId: number): Promise<any[]> {
    const response = await this.api.get(`/monitors/${monitorId}/inmate-links`);
    return response.data;
  }

  async createMonitorInmateLink(monitorId: number, data: {
    inmate_id: number;
    is_excluded: boolean;
    link_reason?: string;
  }): Promise<any> {
    const response = await this.api.post(`/monitors/${monitorId}/inmate-links`, data);
    return response.data;
  }

  async updateMonitorInmateLink(monitorId: number, linkId: number, data: {
    is_excluded: boolean;
    link_reason?: string;
  }): Promise<any> {
    const response = await this.api.put(`/monitors/${monitorId}/inmate-links/${linkId}`, data);
    return response.data;
  }

  async deleteMonitorInmateLink(monitorId: number, linkId: number): Promise<{ message: string }> {
    const response = await this.api.delete(`/monitors/${monitorId}/inmate-links/${linkId}`);
    return response.data;
  }

  async getUserMonitors(userId: number): Promise<PaginatedResponse<Monitor>> {
    const response = await this.api.get(`/users/${userId}/monitors`);
    return response.data;
  }

  // Jails
  async getJails(): Promise<Jail[]> {
    const response = await this.api.get('/jails');
    return response.data;
  }

  async getJail(id: string): Promise<Jail> {
    const response = await this.api.get(`/jails/${id}`);
    return response.data;
  }

  async updateJail(id: string, jail: Partial<Jail>): Promise<Jail> {
    const response = await this.api.put(`/jails/${id}`, jail);
    return response.data;
  }

  // Users (Admin only)
  async getUsers(): Promise<User[]> {
    const response = await this.api.get('/users');
    return response.data;
  }

  async createUser(user: {
    username: string;
    email: string;
    password: string;
    is_active: boolean;
    groups: string[];
  }): Promise<User> {
    const response = await this.api.post('/users', user);
    return response.data;
  }

  async updateUser(id: number, user: Partial<User>): Promise<User> {
    const response = await this.api.put(`/users/${id}`, user);
    return response.data;
  }

  async getGroups(): Promise<Group[]> {
    const response = await this.api.get('/groups');
    return response.data;
  }

  async addUserToGroup(userId: number, groupName: string): Promise<void> {
    await this.api.post(`/users/${userId}/groups`, { group_name: groupName });
  }

  async removeUserFromGroup(userId: number, groupName: string): Promise<void> {
    await this.api.delete(`/users/${userId}/groups/${groupName}`);
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get('/auth/me');
    return response.data;
  }

  async changePassword(data: { currentPassword: string; newPassword: string }): Promise<void> {
    await this.api.post('/auth/change-password', {
      current_password: data.currentPassword,
      new_password: data.newPassword,
    });
  }

  async generateMyApiKey(): Promise<{ api_key: string }> {
    const response = await this.api.post('/my/generate-api-key');
    return response.data;
  }

  async deleteUser(id: number): Promise<void> {
    await this.api.delete(`/users/${id}`);
  }

  async generateApiKey(userId: number): Promise<{ message: string; user_id: number; username: string; api_key: string }> {
    const response = await this.api.post(`/users/${userId}/generate-api-key`);
    return response.data;
  }

  async linkMonitor(monitorId: number, linkData: { linked_monitor_id: number; link_reason?: string }): Promise<void> {
    await this.api.post(`/monitors/${monitorId}/link`, linkData);
  }
}

export const apiService = new ApiService();
