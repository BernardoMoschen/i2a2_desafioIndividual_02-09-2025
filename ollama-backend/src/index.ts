import express from 'express';
import { OllamaService } from './services/ollamaService';

const app = express();
const port = process.env.PORT || 3000;

const ollamaService = new OllamaService();

app.use(express.json());

// Define routes
app.post('/ollama/start', async (req, res) => {
    try {
        await ollamaService.startContainer();
        res.status(200).send('Ollama Mistral container started successfully.');
    } catch (error) {
        res.status(500).send('Error starting Ollama Mistral container: ' + error.message);
    }
});

app.post('/ollama/stop', async (req, res) => {
    try {
        await ollamaService.stopContainer();
        res.status(200).send('Ollama Mistral container stopped successfully.');
    } catch (error) {
        res.status(500).send('Error stopping Ollama Mistral container: ' + error.message);
    }
});

// Start the server
app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});