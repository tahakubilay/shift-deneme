// src/pages/IsteklerimPage.js

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { jwtDecode } from "jwt-decode";
import { Container, Typography, Paper, List, ListItem, ListItemText, Button, Divider, Box, Chip } from '@mui/material';

function IsteklerimPage() {
    const [gelenIstekler, setGelenIstekler] = useState([]);
    const [gidenIstekler, setGidenIstekler] = useState([]);
    const [kullanici, setKullanici] = useState(null);

    const getAuthHeaders = () => {
        const token = localStorage.getItem('accessToken');
        return { headers: { 'Authorization': `Bearer ${token}` } };
    };
    
    useEffect(() => {
        const token = localStorage.getItem('accessToken');
        if (token) {
            try {
                const decodedToken = jwtDecode(token);
                setKullanici(decodedToken);
            } catch (error) {
                console.error("Token çözümlenirken hata:", error);
            }
        }
    }, []);

    const fetchIstekler = () => {
        if (!kullanici) return;

        axios.get('http://127.0.0.1:8000/api/schedules/istekler/', getAuthHeaders())
            .then(response => {
                // ID'leri karşılaştırarak doğru filtreleme
                const gelen = response.data.filter(istek => istek.hedef_calisan === kullanici.user_id && istek.durum === 'hedef_onayi_bekliyor');
                const giden = response.data.filter(istek => istek.istek_yapan === kullanici.user_id);
                
                setGelenIstekler(gelen);
                setGidenIstekler(giden);
            })
            .catch(error => console.error("İstekler çekilirken hata!", error));
    };

    useEffect(() => {
        if (kullanici) {
            fetchIstekler();
        }
    }, [kullanici]);

    const handleYanit = (istekId, yanit) => {
        axios.post(`http://127.0.0.1:8000/api/schedules/istekler/${istekId}/yanitla/`, { yanit: yanit }, getAuthHeaders())
            .then(() => {
                fetchIstekler();
            })
            .catch(error => console.error("Yanıt gönderilirken hata!", error));
    };

    return (
        <Container maxWidth="md" sx={{ mt: 4 }}>
            <Typography component="h1" variant="h4" gutterBottom>
                Vardiya Takas İsteklerim
            </Typography>

            <Paper sx={{ p: 2, mb: 3 }}>
                <Typography variant="h6" gutterBottom>Gelen İstekler</Typography>
                <List>
                    {gelenIstekler.length > 0 ? gelenIstekler.map((istek, index) => (
                        <React.Fragment key={istek.id}>
                            <ListItem>
                                <ListItemText 
                                    primary={`${istek.istek_yapan_adi} kullanıcısı, ${new Date(istek.vardiya.baslangic_zamani).toLocaleString('tr-TR')} vardiyanızı almak istiyor.`}
                                />
                                <Box>
                                    <Button variant="contained" color="success" sx={{ mr: 1 }} onClick={() => handleYanit(istek.id, 'onayla')}>Onayla</Button>
                                    <Button variant="contained" color="error" onClick={() => handleYanit(istek.id, 'reddet')}>Reddet</Button>
                                </Box>
                            </ListItem>
                            {index < gelenIstekler.length - 1 && <Divider />}
                        </React.Fragment>
                    )) : <Typography>Size gelen bir takas isteği yok.</Typography>}
                </List>
            </Paper>

            <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Gönderdiğim İstekler</Typography>
                <List>
                    {gidenIstekler.length > 0 ? gidenIstekler.map((istek, index) => (
                        <React.Fragment key={istek.id}>
                            <ListItem>
                                <ListItemText 
                                    primary={`${new Date(istek.vardiya.baslangic_zamani).toLocaleString('tr-TR')} vardiyanız için ${istek.hedef_calisan_adi} kullanıcısına gönderilen istek.`}
                                />
                                <Chip label={istek.durum.replace(/_/g, ' ').toUpperCase()} color="primary" />
                            </ListItem>
                            {index < gelenIstekler.length - 1 && <Divider />}
                        </React.Fragment>
                    )) : <Typography>Gönderdiğiniz bir takas isteği yok.</Typography>}
                </List>
            </Paper>
        </Container>
    );
}

export default IsteklerimPage;