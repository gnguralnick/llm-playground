import { backendFetch } from '../../hooks';
import { useState } from 'react';
import styles from './signup.module.scss';
import { useNavigate } from 'react-router-dom';

interface SignupFormData {
    email: string;
    password: string;
    confirmPassword: string;
}

export default function Signup() {

    const navigate = useNavigate();
    const [error, setError] = useState<string | null>(null);
    const [form, setForm] = useState<SignupFormData>({
        email: '',
        password: '',
        confirmPassword: ''
    });

    const signup = async () => {
        if (form.password !== form.confirmPassword) {
            setError('Passwords do not match');
            return;
        }

        console.log('signing up');
        try {
            await backendFetch('/users/', {
                method: 'POST',
                body: JSON.stringify({ email: form.email, password: form.password }),
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            navigate('/login');
        } catch {
            setError('Error signing up. User may already exist');
        }
    }

    return (
        <div className={styles.signupPage}>
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
                <div className={styles.formItem}>
                    <label htmlFor="confirmPassword">Confirm Password</label>
                    <input type="password" id='confirmPassword' value={form.confirmPassword} onChange={(e) => setForm({...form, confirmPassword: e.target.value})} />
                </div>
                <button type="submit" className={styles.formSubmit} onClick={e => {e.preventDefault(); void signup()}}>Login</button>
            </form>
            {error && <p className={styles.error}>{error}</p>}
        </div>
    );
}