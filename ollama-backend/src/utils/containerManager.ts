import { exec } from 'child_process';

export function manageContainer(action: 'start' | 'stop'): Promise<string> {
    return new Promise((resolve, reject) => {
        const command = action === 'start' ? 'docker run -d ollama/mistral' : 'docker stop ollama-mistral-container';
        
        exec(command, (error, stdout, stderr) => {
            if (error) {
                reject(`Error: ${stderr}`);
                return;
            }
            resolve(stdout);
        });
    });
}