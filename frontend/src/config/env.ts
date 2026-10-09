import { z } from "zod";

const envSchema = z.object({
  VITE_AEGIS_ENV: z.enum(["local", "dev", "demo"]).default("local"),
  VITE_USE_EMULATORS: z
    .string()
    .optional()
    .transform((v) => v === "true")
    .default("true"),
  VITE_FIREBASE_PROJECT_ID: z.string().default("aegis-fraud-ops-dev"),
  VITE_FIREBASE_API_KEY: z.string().default("mock-api-key-for-local"),
  VITE_FIREBASE_AUTH_DOMAIN: z.string().default("localhost"),
  VITE_FIREBASE_APP_ID: z.string().default("1:1234567890:web:abcdef123456"),
});

export const env = envSchema.parse(import.meta.env);
