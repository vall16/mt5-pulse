export interface Server {
  id?: number;
  user: string;
  pwd: string;
  server: string;
  server_alias:string;
  platform: string;
  ip: string;
  path:string;
  port: number;
  is_active: boolean;
  sort_order?: number;
  created_at: string;
  updated_at: string;
  login:string;
  password:string;
  runtimeStatus?: 'online' | 'offline'; // ✅ nuovo campo opzionale


}
