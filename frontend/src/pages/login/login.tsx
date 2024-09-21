import { useUser } from '../../hooks';
import { useState } from 'react';
import styles from './login.module.scss';

interface LoginFormData {
    email: string;
    password: string;
}

export default function Login() {

    const { login } = useUser();
    const [error, setError] = useState<string | null>(null);
    const [form, setForm] = useState<LoginFormData>({
        email: '',
        password: ''
    });

    const onSubmit = (async () => {
        const formData = new FormData();
        formData.append('username', form.email);
        formData.append('password', form.password);
        try {
            await login(formData);
        } catch {
            setError('Invalid email or password');
        }
    })

    return (
        <div className={styles.loginPage}>
            <h1>Login</h1>
            <form className={styles.form}>
                <div className={styles.formItem}>
                    <label htmlFor="email">Email</label>
                    <input type="email" id='email' value={form.email} onChange={(e) => setForm({...form, email: e.target.value})} />
                </div>
                <div className={styles.formItem}>
                    <label htmlFor="password">Password</label>
                    <input type="password" id='password' value={form.password} onChange={(e) => setForm({...form, password: e.target.value})} />
                </div>
                <button type="submit" className={styles.formSubmit} onClick={e => {e.preventDefault(); void onSubmit()}}>Login</button>
            </form>
            {error && <p className={styles.error}>{error}</p>}
        </div>
    );
}