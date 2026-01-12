export type User = {
  id: number;
  email: string;
};

export async function getUsers(): Promise<User[]> {
  const res = await fetch('/api/users');

  if (!res.ok) {
    throw new Error('Failed to fetch users');
  }

  return res.json();
}

export async function createUser(input: { email: string }): Promise<User> {
  const res = await fetch('/api/users', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  });

  if (res.status === 409) {
    throw new Error('USER_EXISTS');
  }

  if (!res.ok) {
    throw new Error('Failed to create user');
  }

  return res.json();
}
