// kafkaProducer.js
import { Kafka } from "kafkajs";

const kafka = new Kafka({
  clientId: `${process.env.KAFAK_CLIENT_ID}`,
  brokers: [`${process.env.KAFKA_ENVIRONEMENT}:${process.env.KAFKA_PORT}`],
});

export const producer = kafka.producer();

export const sendLog = async (message) => {
  await producer.send({
    topic: `${process.env.KAFKA_TOPIC}`,
    messages: [{ value: JSON.stringify(message) }],
  });
  console.log("📩 Message sent:", message);
};
