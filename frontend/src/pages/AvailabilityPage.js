// src/pages/AvailabilityPage.js

import React, { useState, useEffect } from 'react';
import axios from 'axios';

// --- MUI Bileşenlerini Import Ediyoruz ---
import {
    Container, Typography, Box, Paper, Button, Select, MenuItem, FormControl, InputLabel, Alert
} from '@mui/material';
// ----------------------------------------

function AvailabilityPage() {
    const gunler = [
        { id: 1, ad: 'Pazartesi' }, { id: 2, ad: 'Salı' }, { id: 3, ad: 'Çarşamba' },
        { id: 4, ad: 'Perşembe' }, { id: 5, ad: 'Cuma' }, { id: 6, ad: 'Cumartesi' }, { id: 7, ad: 'Pazar' }
    ];
    const durumlar = ['müsait değil', 'tüm gün', '11 sonrası', '14 sonrası', '17 sonrası'];

    const [sablon, setSablon] = useState({});
    const [mesaj, setMesaj] = useState('');

    const getAuthHeaders = () => {
        const token = localStorage.getItem('accessToken');
        return { headers: { 'Authorization': `Bearer ${token}` } };
    };

    useEffect(() => {
        axios.get('http://127.0.0.1:8000/api/schedules/musaitlik/', getAuthHeaders())
            .then(response => {
                const mevcutSablon = {};
                response.data.forEach(item => {
                    mevcutSablon[item.gun] = item.musaitlik_durumu;
                });
                setSablon(mevcutSablon);
            })
            .catch(error => console.error("Müsaitlik verisi çekilirken hata!", error));
    }, []);

    const handleDurumChange = (gunId, yeniDurum) => {
        setSablon(prevSablon => ({
            ...prevSablon,
            [gunId]: yeniDurum
        }));
    };

    const handleSubmit = (event) => {
        event.preventDefault();
        setMesaj('');

        const gonderilecekVeri = {
            sablon: Object.keys(sablon).map(gunId => ({
                gun: parseInt(gunId),
                musaitlik_durumu: sablon[gunId] || 'müsait değil' // Eğer seçilmemişse varsayılan olarak gönder
            }))
        };

        axios.post('http://127.0.0.1:8000/api/schedules/musaitlik/', gonderilecekVeri, getAuthHeaders())
            .then(() => {
                setMesaj('Müsaitlik durumu başarıyla kaydedildi!');
            })
            .catch(error => {
                setMesaj('Bir hata oluştu. Lütfen tekrar deneyin.');
                console.error("Müsaitlik kaydedilirken hata!", error);
            });
    };

    return (
        <Container maxWidth="sm" sx={{ mt: 4 }}>
            <Paper sx={{ p: 3 }}>
                <Typography component="h1" variant="h4" gutterBottom>
                    Haftalık Müsaitlik Şablonu
                </Typography>
                <Typography paragraph color="text.secondary">
                    Bu şablon, ilgili ay boyunca her hafta için geçerli olacaktır. Lütfen her gün için müsaitlik durumunuzu belirtin.
                </Typography>
                <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
                    {gunler.map(gun => (
                        <FormControl fullWidth key={gun.id} sx={{ mb: 2 }}>
                            <InputLabel id={`label-${gun.id}`}>{gun.ad}</InputLabel>
                            <Select
                                labelId={`label-${gun.id}`}
                                value={sablon[gun.id] || 'müsait değil'}
                                label={gun.ad}
                                onChange={(e) => handleDurumChange(gun.id, e.target.value)}
                            >
                                {durumlar.map(durum => (
                                    <MenuItem key={durum} value={durum}>{durum}</MenuItem>
                                ))}
                            </Select>
                        </FormControl>
                    ))}
                    <Button type="submit" variant="contained" size="large" sx={{ mt: 2 }}>
                        Kaydet
                    </Button>
                </Box>
                {mesaj && <Alert severity="success" sx={{ mt: 2 }}>{mesaj}</Alert>}
            </Paper>
        </Container>
    );
}

export default AvailabilityPage;