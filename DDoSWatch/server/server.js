import dotenv from "dotenv";
dotenv.config();
import express from "express";
import { faker } from "@faker-js/faker";
import { producer, sendLog } from "./kafka_producer.js";

const app = express();
const PORT = process.env.PORT;

async function generateRandomLog() {
  return {
    timestamp: new Date().toISOString(),
    client_ip: faker.internet.ip(),
    method: faker.helpers.arrayElement(["GET", "POST", "PUT", "DELETE"]),
    path: faker.helpers.arrayElement([
      "/api/login",
      "/api/user",
      "/api/pay",
      "/home",
      "/search",
    ]),
    status: faker.helpers.arrayElement([200, 401, 403, 404, 500]),
    response_time_ms: faker.number.int({ min: 50, max: 2000 }),
    request_size: faker.number.int({ min: 200, max: 2048 }),
    user_agent: faker.internet.userAgent(),
    asn: faker.string.alphanumeric(6),
    country: faker.location.countryCode(),
  };
}

app.get("/start", async (req, res) => {
  res.send("Traffic generation started. Check Kafka!");

  console.log(" Connecting Kafka Producer...");
  await producer.connect();

  setInterval(async () => {
    const log = await generateRandomLog();
    await sendLog(log);
    console.log("📩 Sent →", log);
  }, 1000); // Sends log every second
});

app.listen(PORT, () =>
  console.log(`🚀 Server running on http://localhost:${PORT}`)
);
