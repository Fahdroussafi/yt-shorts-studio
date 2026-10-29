import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { Logger } from '@nestjs/common';

async function bootstrap() {
  const logger = new Logger('NestJS-YTAuthBootstrap');
  const app = await NestFactory.create(AppModule);

  app.enableCors({
    origin: true,
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
  });

  app.setGlobalPrefix('api');

  const port = process.env.AUTH_PORT ? parseInt(process.env.AUTH_PORT, 10) : 8051;
  await app.listen(port, '0.0.0.0');

  logger.log(`=======================================================`);
  logger.log(`[*] YouTube Shorts Studio NestJS Auth Service Active`);
  logger.log(`[*] Local URL:    http://localhost:${port}/api/auth/health`);
  logger.log(`[*] Direct Port:  ${port}`);
  logger.log(`[*] JWT Secret:   Active (HS256 7-day expiration)`);
  logger.log(`=======================================================`);
}

bootstrap();
