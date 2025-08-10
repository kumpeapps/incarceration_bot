import axios, { AxiosInstance } from 'axios';
import {
  Inmate,
  Monitor,
  Jail,
  User,
  LoginRequest,
  LoginResponse,
  InmateSearchParams,
  MonitorSearchParams,
  PaginatedResponse,
  DashboardStats,
} from '../types';

class ApiService {
  private api: AxiosInstance;

  constructor() {
    this.api = axios.create({
      baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
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

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get('/auth/me');
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

  async createUser(user: Omit<User, 'id' | 'created_at' | 'last_login' | 'updated_at'> & { password: string }): Promise<User> {
    const response = await this.api.post('/users', user);
    return response.data;
  }

  async updateUser(id: number, user: Partial<User>): Promise<User> {
    const response = await this.api.put(`/users/${id}`, user);
    return response.data;
  }

  async deleteUser(id: number): Promise<void> {
    await this.api.delete(`/users/${id}`);
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await this.api.post('/auth/change-password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
  }

  async linkMonitor(monitorId: number, linkData: { linked_monitor_id: number; link_reason?: string }): Promise<void> {
    await this.api.post(`/monitors/${monitorId}/link`, linkData);
  }
}

export const apiService = new ApiService();
