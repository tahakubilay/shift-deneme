// src/components/Navbar.js

import React from 'react';
// React Router'dan Link'i, MUI'nin kendi Link bileşeniyle karışmaması için RouterLink olarak import ediyoruz
import { Link as RouterLink, useNavigate } from 'react-router-dom';

// --- MUI Bileşenlerini Import Ediyoruz ---
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
// ----------------------------------------

function Navbar() {
    const navigate = useNavigate();
    const token = localStorage.getItem('accessToken');

    const handleLogout = () => {
        localStorage.removeItem('accessToken');
        navigate('/login');
        // Sayfanın tamamen yenilenip state'in temizlenmesi için
        window.location.reload();
    };

    // Eğer kullanıcı giriş yapmamışsa (token yoksa), Navbar'ı hiç gösterme.
    if (!token) {
        return null;
    }

    return (
        <AppBar position="static">
            <Toolbar>
                {/* Sol taraftaki başlık */}
                <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                    Vardiya Sistemi
                </Typography>

                {/* Sağ taraftaki menü linkleri ve buton */}
                <Box>
                    <Button color="inherit" component={RouterLink} to="/takvim">
                        Vardiya Takvimi
                    </Button>
                    <Button color="inherit" component={RouterLink} to="/isteklerim">İsteklerim</Button>
                    <Button color="inherit" component={RouterLink} to="/musaitlik">
                        Müsaitliğimi Bildir
                    </Button>
                    <Button color="inherit" component={RouterLink} to="/subeler">
                        Şubeler
                    </Button>
                    <Button color="inherit" component={RouterLink} to="/kullanicilar">
                        Kullanıcılar
                    </Button>
                    <Button color="inherit" onClick={handleLogout}>
                        Çıkış Yap
                    </Button>
                </Box>
            </Toolbar>
        </AppBar>
    );
}

export default Navbar;