// server.js
import express from "express";
import bodyParser from "body-parser";
import { Configuration, OpenAIApi } from "openai";
import mysql from "mysql2/promise";

const app = express();
app.use(bodyParser.json());

// --- OpenAI setup ---
const configuration = new Configuration({
    apiKey: process.env.OPENAI_API_KEY,
});
const openai = new OpenAIApi(configuration);

// --- Database config ---
const dbConfig = {
    host: "localhost",
    user: "crm",
    password: "vd12kgum20",
    database: "leads_db",
};

// --- Insert lead into DB ---
async function saveLead(lead) {
    const conn = await mysql.createConnection(dbConfig);
    await conn.execute(
        `INSERT INTO leads (name,email,phone,service_type,status,created_at) VALUES (?,?,?,?,?,NOW())`,
        [lead.name, lead.email, lead.phone, lead.service_type, lead.status || "Pending"]
    );
    await conn.end();
}

// --- In-memory conversation states per user session ---
const sessions = {}; // { sessionId: { collectedLead, history } }

app.post("/chat", async (req, res) => {
    const { sessionId, message } = req.body;
    if (!sessionId) return res.status(400).json({ error: "sessionId required" });

    // Initialize session if new
    if (!sessions[sessionId]) {
        sessions[sessionId] = {
            collectedLead: { name:"", email:"", phone:"", service_type:"" },
            history: []
        };
    }
    const session = sessions[sessionId];

    // Build prompt for GPT
    const prompt = `
You are a solar energy lead assistant. 
Collected lead so far: ${JSON.stringify(session.collectedLead)}
User message: ${message}

Tasks:
- Identify if user provided any missing info (name, email, phone, service_type).
- If info is missing, ask politely for it step by step.
- Once all fields are collected, respond "Lead complete" and provide JSON like: 
{"name":"...","email":"...","phone":"...","service_type":"..."}
- Otherwise, continue conversation.
`;

    // Add user message to history
    session.history.push({ role: "user", content: message });

    try {
        const response = await openai.chat.completions.create({
            model: "gpt-4-mini",
            messages: [{ role: "user", content: prompt }],
            temperature: 0.7,
        });

        const aiText = response.choices[0].message.content;

        // Attempt to parse lead JSON
        let leadComplete = false;
        try {
            const jsonMatch = aiText.match(/\{[\s\S]*\}/);
            if (jsonMatch) {
                const leadData = JSON.parse(jsonMatch[0]);
                // Save lead in DB
                await saveLead(leadData);
                leadComplete = true;
                // Reset session collected lead
                sessions[sessionId].collectedLead = { name:"", email:"", phone:"", service_type:"" };
            }
        } catch (err) {
            // Not complete yet
        }

        res.json({ reply: aiText, leadComplete });

    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Internal server error" });
    }
});

app.listen(3000, () => console.log("AI Lead Assistant running on port 3000"));
