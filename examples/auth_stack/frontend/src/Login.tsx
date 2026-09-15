import React from 'react';
import { showError } from './errors';

export function Login() {
  async function submit(username: string, password: string) {
    const response = await fetch('/login', {
      method: 'POST',
      body: JSON.stringify({ username, password })
    });
    if (!response.ok) showError('Login failed');
  }
  return <button onClick={() => submit('demo', 'password')}>Log in</button>;
}
