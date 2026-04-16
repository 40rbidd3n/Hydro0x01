import { z } from 'zod'

const envSchema = z.object({
  MQTT_BROKER: z.string(),
  MQTT_PORT: z.string().optional(),
  MQTT_USER: z.string().optional(),
  MQTT_PASSWORD: z.string().optional(),
  MQTT_BASE_TOPIC: z.string().default('HydroponicOne'),

  INFLUX_URL: z.string(),
  INFLUX_TOKEN: z.string(),
  INFLUX_ORG: z.string(),
  INFLUX_BUCKET: z.string(),

  DATABASE_URL: z.string(),

  //OTA_PRIVATE_KEY_PATH: z.string(),

  PORT: z.string().default('3000'),
  FRONTEND_ORIGIN: z.string().default('http://localhost:5173'),

  JWT_SECRET: z.string().default('openhydro_super_secret_jwt_key_develop_only'),
})

export type Env = ReturnType<typeof validateEnv>;

export function validateEnv() {
  const parsed = envSchema.safeParse(process.env)
  if (!parsed.success) {
    console.error('Invalid environment variables', parsed.error.format())
    process.exit(1)
  }
  const env = parsed.data
  return {
    MQTT_BROKER: env.MQTT_BROKER,
    MQTT_PORT: parseInt(env.MQTT_PORT || '8883', 10),
    MQTT_USER: env.MQTT_USER,
    MQTT_PASSWORD: env.MQTT_PASSWORD,
    MQTT_BASE_TOPIC: env.MQTT_BASE_TOPIC,
    INFLUX_URL: env.INFLUX_URL,
    INFLUX_TOKEN: env.INFLUX_TOKEN,
    INFLUX_ORG: env.INFLUX_ORG,
    INFLUX_BUCKET: env.INFLUX_BUCKET,
    DATABASE_URL: env.DATABASE_URL,
    //OTA_PRIVATE_KEY_PATH: env.OTA_PRIVATE_KEY_PATH,
    PORT: parseInt(env.PORT, 10),
    FRONTEND_ORIGIN: env.FRONTEND_ORIGIN,
    JWT_SECRET: env.JWT_SECRET,
  }
}
