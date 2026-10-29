import { Injectable, BadRequestException, UnauthorizedException, ConflictException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcryptjs';
import { UsersService } from '../users/users.service';
import { RegisterDto, LoginDto } from './dto/auth.dto';

@Injectable()
export class AuthService {
  constructor(
    private readonly usersService: UsersService,
    private readonly jwtService: JwtService
  ) {}

  private validateEmail(email: string): boolean {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
  }

  async register(dto: RegisterDto): Promise<{ access_token: string; user: { id: string; email: string; name?: string } }> {
    if (!dto.email || !this.validateEmail(dto.email)) {
      throw new BadRequestException('Please provide a valid email address');
    }

    if (!dto.password || dto.password.length < 6) {
      throw new BadRequestException('Password must be at least 6 characters long');
    }

    const existing = await this.usersService.findByEmail(dto.email);
    if (existing) {
      throw new ConflictException('An account with this email already exists');
    }

    const salt = bcrypt.genSaltSync(10);
    const passwordHash = bcrypt.hashSync(dto.password, salt);

    const user = await this.usersService.create(dto.email, passwordHash, dto.name);
    const payload = { sub: user.id, email: user.email };
    const access_token = this.jwtService.sign(payload);

    return {
      access_token,
      user: {
        id: user.id,
        email: user.email,
        name: user.name
      }
    };
  }

  async login(dto: LoginDto): Promise<{ access_token: string; user: { id: string; email: string; name?: string } }> {
    if (!dto.email || !dto.password) {
      throw new BadRequestException('Email and password are required');
    }

    const user = await this.usersService.findByEmail(dto.email);
    if (!user) {
      throw new UnauthorizedException('Invalid email or password');
    }

    const match = bcrypt.compareSync(dto.password, user.passwordHash);
    if (!match) {
      throw new UnauthorizedException('Invalid email or password');
    }

    const payload = { sub: user.id, email: user.email };
    const access_token = this.jwtService.sign(payload);

    return {
      access_token,
      user: {
        id: user.id,
        email: user.email,
        name: user.name
      }
    };
  }

  async verifyToken(token: string): Promise<{ valid: boolean; user?: any; error?: string }> {
    try {
      const payload = this.jwtService.verify(token);
      const user = await this.usersService.findById(payload.sub);
      if (!user) {
        return { valid: false, error: 'User not found' };
      }
      return {
        valid: true,
        user: { id: user.id, email: user.email, name: user.name }
      };
    } catch (err: any) {
      return { valid: false, error: err.message };
    }
  }
}
