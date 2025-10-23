// frontend/src/pages/LoginPage.js

import React, { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { Button, TextField, Container, Typography, Box, Alert } from '@mui/material';

function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = (event) => {
        event.preventDefault();
        setError('');

        axios.post('http://127.0.0.1:8000/api/auth/login/', {
            username: username,
            password: password,
        })
        .then(response => {
            // --- KESİN DÜZELTME BURADA ---
            // Backend'den 'access' (alt çizgisiz) ve 'user' objelerini al
            const token = response.data.access; 
            const user = response.data.user;
            // -----------------------------

            if (token && user) {
                // Hem token'ı hem de kullanıcı bilgisini hafızaya kaydet
                localStorage.setItem('accessToken', token);
                localStorage.setItem('currentUser', JSON.stringify(user)); // Kullanıcıyı JSON olarak sakla
                
                navigate('/takvim');
                window.location.reload(); // Navbar'ın güncellenmesi için
            } else {
                setError("Giriş başarılı ama token veya kullanıcı bilgisi alınamadı. Yanıt: " + JSON.stringify(response.data));
            }
        })
        .catch(error => {
            console.error("Giriş hatası!", error);
            setError('Kullanıcı adı veya şifre hatalı.');
        });
    };

    return (
        <Container component="main" maxWidth="xs">
            <Box
                sx={{
                    marginTop: 8,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                }}
            >
                <Typography component="h1" variant="h5">
                    Vardiya Sistemi - Giriş Yap
                </Typography>
                <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        id="username"
                        label="Kullanıcı Adı"
                        name="username"
                        autoComplete="username"
                        autoFocus
                        value={username}
                        onChange={e => setUsername(e.target.value)}
                    />
                    <TextField
                        margin="normal"
                        required
                        fullWidth
                        name="password"
                        label="Şifre"
                        type="password"
                        id="password"
                        autoComplete="current-password"
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                    />
                    
                    {error && <Alert severity="error" sx={{ mt: 1 }}>{error}</Alert>}
                    
                    <Button
                        type="submit"
                        fullWidth
                        variant="contained"
                        sx={{ mt: 3, mb: 2 }}
                    >
                        Giriş Yap
                    </Button>
                </Box>
            </Box>
        </Container>
    );
}

export default LoginPage;