import { Injectable, Logger } from '@nestjs/common';
import * as fs from 'fs';
import * as path from 'path';

export interface User {
  id: string;
  email: string;
  passwordHash: string;
  name?: string;
  createdAt: string;
}

@Injectable()
export class UsersService {
  private readonly logger = new Logger(UsersService.name);
  private readonly storagePath: string;
  private users: User[] = [];

  constructor() {
    const candidates = [
      path.resolve(process.cwd(), 'users.json'),
      path.resolve(process.cwd(), '..', 'users.json'),
      path.resolve(__dirname, '..', '..', '..', 'users.json'),
      path.resolve(__dirname, '..', '..', 'users.json')
    ];

    let chosenPath = candidates[0];
    for (const p of candidates) {
      const dir = path.dirname(p);
      if (fs.existsSync(dir)) {
        chosenPath = p;
        break;
      }
    }

    this.storagePath = chosenPath;
    this.ensureDirectoryAndLoad();
  }

  private ensureDirectoryAndLoad(): void {
    try {
      const dir = path.dirname(this.storagePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      if (fs.existsSync(this.storagePath)) {
        const raw = fs.readFileSync(this.storagePath, 'utf-8');
        this.users = JSON.parse(raw);
        this.logger.log(`Loaded ${this.users.length} registered users from ${this.storagePath}`);
      } else {
        this.users = [];
        this.saveToFile();
        this.logger.log(`Initialized empty users database at ${this.storagePath}`);
      }
    } catch (err: any) {
      this.logger.error(`Failed to initialize users storage: ${err.message}`);
      this.users = [];
    }
  }

  private saveToFile(): void {
    try {
      fs.writeFileSync(this.storagePath, JSON.stringify(this.users, null, 2), 'utf-8');
    } catch (err: any) {
      this.logger.error(`Failed to persist users: ${err.message}`);
    }
  }

  async findByEmail(email: string): Promise<User | null> {
    const normalized = email.toLowerCase().trim();
    return this.users.find(u => u.email.toLowerCase() === normalized) || null;
  }

  async findById(id: string): Promise<User | null> {
    return this.users.find(u => u.id === id) || null;
  }

  async create(email: string, passwordHash: string, name?: string): Promise<User> {
    const newUser: User = {
      id: 'yt_usr_' + Date.now().toString(36) + Math.random().toString(36).substring(2, 7),
      email: email.toLowerCase().trim(),
      passwordHash,
      name: name?.trim() || email.split('@')[0],
      createdAt: new Date().toISOString()
    };

    this.users.push(newUser);
    this.saveToFile();
    this.logger.log(`New user registered: ${newUser.email} (id: ${newUser.id})`);
    return newUser;
  }

  async count(): Promise<number> {
    return this.users.length;
  }
}
