'use client';

import { useEffect, useState } from 'react';
import { getUsers, createUser, User } from '../lib/api';

export default function Home() {
  const [users, setUsers] = useState<User[]>([]);
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getUsers().then(setUsers).catch(() => {
      setError('Failed to load users');
    });
  }, []);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    try {
      const user = await createUser({ email });
      setUsers(prev => [...prev, user]);
      setEmail('');
    } catch (err: any) {
      if (err.message === 'USER_EXISTS') {
        setError('User already exists');
      } else {
        setError('Create user failed');
      }
    }
  }

  return (
    <main className="p-6 max-w-xl space-y-6">
      <h1 className="text-xl font-bold">Users</h1>

      <form onSubmit={onSubmit} className="space-y-2">
        <input
          className="border p-2 w-full"
          placeholder="Email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          required
        />
        <button className="bg-black text-white px-4 py-2">
          Create user
        </button>
      </form>

      {error && <p className="text-red-600">{error}</p>}

      <ul className="space-y-1">
        {users.map(u => (
          <li key={u.id}>
            {u.email}
          </li>
        ))}
      </ul>
    </main>
  );
}
