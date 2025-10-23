// src/pages/AdminOnayPage.js

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Container, Typography, Paper, List, ListItem, ListItemText, Button, Divider, Box, Chip, Alert } from '@mui/material';

function AdminOnayPage() {
    const [bekleyenIstekler, setBekleyenIstekler] = useState([]);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');

    const getAuthHeaders = () => {
        const token = localStorage.getItem('accessToken');
        return { headers: { 'Authorization': `Bearer ${token}` } };
    };

    const fetchBekleyenIstekler = () => {
        axios.get('http://127.0.0.1:8000/api/schedules/admin/istekler/', getAuthHeaders())
            .then(response => {
                setBekleyenIstekler(response.data);
            })
            .catch(error => {
                console.error("Admin istekleri çekilirken hata!", error);
                setError('Onay bekleyen istekler yüklenemedi.');
            });
    };

    // Sayfa yüklendiğinde istekleri çek
    useEffect(() => {
        fetchBekleyenIstekler();
    }, []);

    const handleAksiyon = (istekId, action) => {
        setError('');
        setSuccess('');
        axios.post(`http://127.0.0.1:8000/api/schedules/admin/istekler/${istekId}/aksiyon/`, { action: action }, getAuthHeaders())
            .then(response => {
                setSuccess(response.data.mesaj);
                // Listeyi yenile
                fetchBekleyenIstekler();
            })
            .catch(error => {
                console.error("Aksiyon gönderilirken hata!", error);
                setError(error.response?.data?.hata || 'İşlem sırasında bir hata oluştu.');
            });
    };

    return (
        <Container maxWidth="md" sx={{ mt: 4 }}>
            <Typography component="h1" variant="h4" gutterBottom>
                Yönetici Onay Bekleyen Takaslar
            </Typography>

            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

            <Paper sx={{ p: 2, mb: 3 }}>
                <List>
                    {bekleyenIstekler.length > 0 ? bekleyenIstekler.map((istek, index) => (
                        <React.Fragment key={istek.id}>
                            <ListItem>
                                <ListItemText 
                                    primary={`[${istek.istek_yapan_adi}] <-> [${istek.hedef_calisan_adi}]`}
                                    secondary={
                                        `TEKLİF: ${istek.istek_yapan_adi}, ${new Date(istek.istek_yapan_vardiya_detay.baslangic_zamani).toLocaleString('tr-TR')} vardiyasını veriyor. | İSTEK: ${istek.hedef_calisan_adi}'in ${new Date(istek.hedef_vardiya_detay.baslangic_zamani).toLocaleString('tr-TR')} vardiyasını istiyor.`
                                    }
                                />
                                <Box sx={{ minWidth: 220 }}> {/* Butonların sıkışmasını engelle */}
                                    <Button variant="contained" color="success" sx={{ mr: 1 }} onClick={() => handleAksiyon(istek.id, 'onayla')}>
                                        Onayla
                                    </Button>
                                    <Button variant="contained" color="error" onClick={() => handleAksiyon(istek.id, 'reddet')}>
                                        Reddet
                                    </Button>
                                </Box>
                            </ListItem>
                            {index < bekleyenIstekler.length - 1 && <Divider />}
                        </React.Fragment>
                    )) : <Typography>Onay bekleyen bir takas isteği yok.</Typography>}
                </List>
            </Paper>
        </Container>
    );
}

export default AdminOnayPage;