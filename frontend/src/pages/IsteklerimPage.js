// src/pages/IsteklerimPage.js (Hata Ayıklama v3)

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
        if (!kullanici) {
            console.log("Kullanıcı bilgisi henüz yok, istek atlanıyor.");
            return;
        }

        axios.get('http://127.0.0.1:8000/api/schedules/istekler/', getAuthHeaders())
            .then(response => {
                // --- DETAYLI HATA AYIKLAMA MESAJLARI ---
                console.log("--- DEBUG v3: Filtreleme Kontrolü ---");
                console.log("API'den Gelen Ham Veri (Tüm İstekler):", response.data);
                console.log("Filtreleme için kullanılan kullanıcı bilgisi (token'dan):", kullanici);

                if (response.data.length > 0 && kullanici) {
                    console.log("--- KARŞILAŞTIRMA ---");
                    console.log("API 'istek_yapan' ID:", response.data[0].istek_yapan, " | Tipi:", typeof response.data[0].istek_yapan);
                    console.log("API 'hedef_calisan' ID:", response.data[0].hedef_calisan, " | Tipi:", typeof response.data[0].hedef_calisan);
                    console.log("Token 'user_id':", kullanici.user_id, " | Tipi:", typeof kullanici.user_id);
                    console.log("GİDEN FİLTRESİ (istek_yapan === user_id):", response.data[0].istek_yapan === kullanici.user_id);
                    console.log("GELEN FİLTRESİ (hedef_calisan === user_id):", response.data[0].hedef_calisan === kullanici.user_id);
                }
                console.log("--------------------------");
                // ------------------------------------

                // --- TİP DÖNÜŞÜMÜ İLE GÜVENLİ FİLTRELEME ---
                const gelen = response.data.filter(istek => 
                    istek.hedef_calisan.toString() === kullanici.user_id.toString() && 
                    istek.durum === 'hedef_onayi_bekliyor'
                );
                const giden = response.data.filter(istek => 
                    istek.istek_yapan.toString() === kullanici.user_id.toString()
                );
                // --------------------------------------------

                console.log("Filtreleme Sonucu (Gelen):", gelen);
                console.log("Filtreleme Sonucu (Giden):", giden);
                
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

            {/* Gelen İstekler */}
            <Paper sx={{ p: 2, mb: 3 }}>
                <Typography variant="h6" gutterBottom>Gelen İstekler</Typography>
                <List>
                    {gelenIstekler.length > 0 ? gelenIstekler.map((istek, index) => (
                        <React.Fragment key={istek.id}>
                            <ListItem>
                                <ListItemText 
                                    // --- DÜZELTME BURADA ---
                                    // Artık iki vardiyanın da bilgisini gösteriyoruz
                                    primary={`${istek.istek_yapan_adi}, sizin ${new Date(istek.hedef_vardiya_detay.baslangic_zamani).toLocaleString('tr-TR')} vardiyanızı istiyor.`}
                                    secondary={`Teklifi: Kendi ${new Date(istek.istek_yapan_vardiya_detay.baslangic_zamani).toLocaleString('tr-TR')} vardiyası.`}
                                    // ---------------------
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

            {/* Giden İstekler */}
            <Paper sx={{ p: 2 }}>
                <Typography variant="h6" gutterBottom>Gönderdiğim İstekler</Typography>
                <List>
                    {gidenIstekler.length > 0 ? gidenIstekler.map((istek, index) => (
                        <React.Fragment key={istek.id}>
                            <ListItem>
                                <ListItemText 
                                    // --- DÜZELTME BURADA ---
                                    primary={`${istek.hedef_calisan_adi}'in ${new Date(istek.hedef_vardiya_detay.baslangic_zamani).toLocaleString('tr-TR')} vardiyası için teklif gönderildi.`}
                                    secondary={`Karşılığında teklif edilen: Sizin ${new Date(istek.istek_yapan_vardiya_detay.baslangic_zamani).toLocaleString('tr-TR')} vardiyanız.`}
                                    // ---------------------
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