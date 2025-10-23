// src/components/Navbar.js

import React, { useState, useEffect } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
// jwtDecode'a artık ihtiyacımız yok
import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';

function Navbar() {
    const navigate = useNavigate();
    const [currentUser, setCurrentUser] = useState(null);

    useEffect(() => {
        // Hafızadaki 'currentUser' objesini oku
        const userString = localStorage.getItem('currentUser');
        if (userString) {
            try {
                setCurrentUser(JSON.parse(userString));
            } catch (e) { console.error("Kullanıcı bilgisi okunurken hata:", e); }
        }
    }, []);

    const handleLogout = () => {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('currentUser'); // Kullanıcıyı da sil
        setCurrentUser(null);
        navigate('/login');
        window.location.reload();
    };

    if (!currentUser) { return null; } // Giriş yapılmadıysa menüyü gösterme

    return (
        <AppBar position="static">
            <Toolbar>
                <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
                    Vardiya Sistemi
                </Typography>
                <Box>
                    {/* Admin linki 'is_staff' bayrağına göre gösterilir */}
                    {currentUser.is_staff && (
                        <Button color="inherit" component={RouterLink} to="/admin/onaylar">
                            Yönetici Onayları
                        </Button>
                    )}
                    <Button color="inherit" component={RouterLink} to="/takvim">
                        Vardiya Takvimi
                    </Button>
                    <Button color="inherit" component={RouterLink} to="/vardiyalarim">Vardiyalarım</Button>
                    <Button color="inherit" component={RouterLink} to="/isteklerim">
                        İsteklerim
                    </Button>
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