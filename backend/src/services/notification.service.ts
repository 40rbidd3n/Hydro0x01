import { createLogger } from '../utils/logger.js';
import { prisma } from '../utils/prisma.js';
import { NotificationIntegration, AlertNotification } from './notification.types.js';

const logger = createLogger();

export async function sendNotification(alert: AlertNotification) {
  try {
    const config = await prisma.systemConfig.findFirst();
    if (!config) return;

    // Dispatch to enabled platforms
    if (config.telegram_enabled && config.telegram_botToken && config.telegram_chatId) {
      await sendTelegram(config.telegram_botToken, config.telegram_chatId, alert)
        .catch(err => logger.error({ err }, 'Failed to send Telegram alert'));
    }

    if (config.discord_enabled && config.discord_webhookUrl) {
      await sendDiscord(config.discord_webhookUrl, alert)
        .catch(err => logger.error({ err }, 'Failed to send Discord alert'));
    }

  } catch (error) {
    logger.error({ error }, 'Failed to process notifications');
  }
}

async function sendTelegram(token: string, chatId: string, alert: AlertNotification) {
  if (!token || !chatId) return;

  // Format message
  const icon = alert.level === 'critical' ? '🚨' : alert.level === 'warning' ? '⚠️' : 'ℹ️';
  let message = `<b>${icon} HydroponicOne Alert</b>\n\n`;
  message += `<b>${alert.title}</b>\n`;
  message += `${alert.message}\n`;
  if (alert.device_id) {
    message += `<i>Device: ${alert.device_id}</i>`;
  }

  const url = `https://api.telegram.org/bot${token}/sendMessage`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      chat_id: chatId,
      text: message,
      parse_mode: 'HTML'
    })
  });

  if (!response.ok) {
    throw new Error(`Telegram API responded with ${response.status}`);
  }
}

async function sendDiscord(webhookUrl: string, alert: AlertNotification) {
  if (!webhookUrl) return;

  const color = alert.level === 'critical' ? 16711680 : alert.level === 'warning' ? 16776960 : 3447003;
  const icon = alert.level === 'critical' ? '🚨' : alert.level === 'warning' ? '⚠️' : 'ℹ️';

  const payload = {
    username: "HydroponicOne System",
    embeds: [
      {
        title: `${icon} ${alert.title}`,
        description: alert.message,
        color: color,
        fields: alert.device_id ? [
          { name: "Device", value: alert.device_id, inline: true }
        ] : []
      }
    ]
  };

  const response = await fetch(webhookUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`Discord API responded with ${response.status}`);
  }
}
