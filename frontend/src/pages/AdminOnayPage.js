// src/pages/AdminOnayPage.js

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Container, Typography, Paper, List, ListItem, ListItemText, Button, Divider, Box, Chip, Alert, Dialog, DialogTitle, DialogContent, DialogActions, FormControl, InputLabel, Select, MenuItem, RadioGroup, FormControlLabel, Radio } from '@mui/material';
import moment from 'moment';

function AdminOnayPage() {
    const [bekleyenIstekler, setBekleyenIstekler] = useState([]);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [openDialog, setOpenDialog] = useState(false);
    const [selectedIstek, setSelectedIstek] = useState(null);
    const [yedekAtansinMi, setYedekAtansinMi] = useState('hayir');
    const [calisanListesi, setCalisanListesi] = useState([]);
    const [selectedYedekId, setSelectedYedekId] = useState('');

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

    const handleAksiyon = (istek, action) => {
        if (istek.istek_tipi === 'iptal' && action === 'onayla') {
            setSelectedIstek(istek);
            setOpenDialog(true);
            fetchCalisanlar();
            return;
        }

        setError('');
        setSuccess('');
        axios.post(`http://127.0.0.1:8000/api/schedules/admin/istekler/${istek.id}/aksiyon/`, { action: action }, getAuthHeaders())
            .then(response => {
                setSuccess(response.data.mesaj);
                fetchBekleyenIstekler();
            })
            .catch(error => {
                console.error("Aksiyon gönderilirken hata!", error);
                setError(error.response?.data?.hata || 'İşlem sırasında bir hata oluştu.');
            });
    };

    const fetchCalisanlar = () => {
        axios.get('http://127.0.0.1:8000/api/kullanicilar/', getAuthHeaders())
            .then(response => setCalisanListesi(response.data))
            .catch(error => console.error("Çalışan listesi çekilemedi!", error));
    };

    const handleDialogClose = () => {
        setOpenDialog(false);
        setSelectedIstek(null);
        setYedekAtansinMi('hayir');
        setSelectedYedekId('');
    };

    const handleDialogConfirm = () => {
        if (!selectedIstek) return;

        setError('');
        setSuccess('');

        const payload = {
            action: 'onayla',
            yedek_calisan_id: yedekAtansinMi === 'evet' ? parseInt(selectedYedekId) : null
        };

        axios.post(`http://127.0.0.1:8000/api/schedules/admin/istekler/${selectedIstek.id}/aksiyon/`, payload, getAuthHeaders())
            .then(response => {
                setSuccess(response.data.mesaj);
                fetchBekleyenIstekler();
                handleDialogClose();
            })
            .catch(error => {
                console.error("İptal onayı sırasında hata!", error);
                setError(error.response?.data?.hata || 'İşlem sırasında bir hata oluştu.');
                handleDialogClose();
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
                                <Box sx={{ minWidth: 220 }}>
                                    {istek.istek_tipi === 'iptal' && (
                                        <Chip label="İPTAL" color="warning" size="small" sx={{ mr: 1 }} />
                                    )}
                                    {istek.istek_tipi === 'takas' && (
                                        <Chip label="TAKAS" color="info" size="small" sx={{ mr: 1 }} />
                                    )}
                                    <Button variant="contained" color="success" sx={{ mr: 1 }} onClick={() => handleAksiyon(istek, 'onayla')}>
                                        Onayla
                                    </Button>
                                    <Button variant="contained" color="error" onClick={() => handleAksiyon(istek, 'reddet')}>
                                        Reddet
                                    </Button>
                                </Box>
                            </ListItem>
                            {index < bekleyenIstekler.length - 1 && <Divider />}
                        </React.Fragment>
                    )) : <Typography>Onay bekleyen bir takas isteği yok.</Typography>}
                </List>
            </Paper>

            <Dialog open={openDialog} onClose={handleDialogClose} maxWidth="sm" fullWidth>
                <DialogTitle>İptal İsteği Onayı</DialogTitle>
                <DialogContent>
                    {selectedIstek && (
                        <Box>
                            <Typography variant="body1" sx={{ mb: 2 }}>
                                <strong>{selectedIstek.istek_yapan_adi}</strong> kullanıcısı, {moment(selectedIstek.istek_yapan_vardiya_detay.baslangic_zamani).format('DD MMM YYYY, HH:mm')} tarihli vardiyasını iptal etmek istiyor.
                            </Typography>
                            <Typography variant="body2" sx={{ mb: 2 }}>
                                <strong>Şube:</strong> {selectedIstek.istek_yapan_vardiya_detay.sube_adi}
                            </Typography>
                            <Divider sx={{ my: 2 }} />
                            <FormControl component="fieldset" fullWidth>
                                <Typography variant="subtitle1" sx={{ mb: 1 }}>Bu kişi yerine birisi atanacak mı?</Typography>
                                <RadioGroup value={yedekAtansinMi} onChange={(e) => setYedekAtansinMi(e.target.value)}>
                                    <FormControlLabel value="hayir" control={<Radio />} label="Hayır, vardiya iptal edilsin" />
                                    <FormControlLabel value="evet" control={<Radio />} label="Evet, yerine birini ata" />
                                </RadioGroup>
                            </FormControl>
                            {yedekAtansinMi === 'evet' && (
                                <FormControl fullWidth sx={{ mt: 2 }}>
                                    <InputLabel>Yedek Çalışan Seç</InputLabel>
                                    <Select
                                        value={selectedYedekId}
                                        label="Yedek Çalışan Seç"
                                        onChange={(e) => setSelectedYedekId(e.target.value)}
                                    >
                                        <MenuItem value=""><em>Seçiniz...</em></MenuItem>
                                        {calisanListesi.filter(c => c.id !== selectedIstek.istek_yapan).map(calisan => (
                                            <MenuItem key={calisan.id} value={calisan.id}>
                                                {calisan.first_name} {calisan.last_name} ({calisan.username})
                                            </MenuItem>
                                        ))}
                                    </Select>
                                </FormControl>
                            )}
                        </Box>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleDialogClose}>İptal</Button>
                    <Button
                        variant="contained"
                        onClick={handleDialogConfirm}
                        disabled={yedekAtansinMi === 'evet' && !selectedYedekId}
                    >
                        Onayla
                    </Button>
                </DialogActions>
            </Dialog>
        </Container>
    );
}

export default AdminOnayPage;