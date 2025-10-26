// src/pages/VardiyalarimPage.js

import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Container, Typography, Paper, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Button, CircularProgress, Box, Alert,
         Modal, Fade, Backdrop, Select, MenuItem, FormControl, InputLabel, List, ListItem, ListItemText, RadioGroup, FormControlLabel, Radio
} from '@mui/material'; // Modal için gerekli bileşenleri ekledik
import moment from 'moment';
import { jwtDecode } from "jwt-decode";
import { useNavigate } from 'react-router-dom';
// Modal için stil
const modalStyle = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 600, // Modalı biraz genişletelim
    bgcolor: 'background.paper',
    border: '2px solid #000',
    boxShadow: 24,
    p: 4,
    maxHeight: '90vh',
    overflowY: 'auto'
};

function VardiyalarimPage() {
    const [vardiyalar, setVardiyalar] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [success, setSuccess] = useState('');
    const [currentUser, setCurrentUser] = useState(null);

    // --- YENİ MODAL STATE'LERİ ---
    const [openModal, setOpenModal] = useState(false);
    const [selectedVardiya, setSelectedVardiya] = useState(null); // Takas etmek istediğimiz KENDİ vardiyamız
    const [colleagues, setColleagues] = useState([]); // Çalışma arkadaşları listesi
    const [selectedColleagueId, setSelectedColleagueId] = useState(''); // Seçilen arkadaşın ID'si
    const [allColleagueShifts, setAllColleagueShifts] = useState([]); // Seçilen arkadaşın TÜM vardiyaları
    const [selectedColleagueShiftId, setSelectedColleagueShiftId] = useState(''); // Seçilen arkadaş vardiyasının ID'si
    const [tradeError, setTradeError] = useState('');
    // ----------------------------

    const getAuthHeaders = () => {
        const token = localStorage.getItem('accessToken');
        return { headers: { 'Authorization': `Bearer ${token}` } };
    };

    // Kullanıcı bilgisini token'dan al
    useEffect(() => {
        const token = localStorage.getItem('accessToken');
        if (token) {
            try { setCurrentUser(jwtDecode(token)); } catch (e) { console.error("Token error", e); }
        }
    }, []);

    // Sadece kendi vardiyalarımızı çeken fonksiyon
    const fetchBenimVardiyalarim = useCallback(() => {
        setLoading(true);
        axios.get('http://127.0.0.1:8000/api/schedules/vardiyalarim/', getAuthHeaders())
            .then(response => {
                setVardiyalar(response.data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Vardiyalarım çekilirken hata:", err);
                setError("Vardiyalarınız yüklenirken bir sorun oluştu.");
                setLoading(false);
            });
    }, []);

    useEffect(() => {
        if (currentUser) {
            fetchBenimVardiyalarim();
        }
    }, [currentUser, fetchBenimVardiyalarim]);

    // --- YENİ FONKSİYONLAR ---

    // Takas Et butonuna basıldığında modalı açar ve verileri hazırlar
    const handleTakasBaslat = (vardiya) => {
        setSelectedVardiya(vardiya); // Kendi vardiyamızı seçtik
        setOpenModal(true);
        setTradeError('');
        setSelectedColleagueId('');
        setAllColleagueShifts([]);
        setSelectedColleagueShiftId('');
        fetchColleagues(); // Çalışan listesini çek
    };

    const handleCloseModal = () => setOpenModal(false);

    // Çalışma arkadaşlarını çeker
    const fetchColleagues = () => {
        if (!currentUser) return;
        axios.get('http://127.0.0.1:8000/api/kullanicilar/', getAuthHeaders())
            .then(response => {
                const others = response.data.filter(user => user.id !== currentUser.user_id);
                setColleagues(others);
            })
            .catch(error => console.error("Çalışan listesi çekilirken hata!", error));
    };

    // Arkadaş seçildiğinde, onun TÜM vardiyalarını çeker
    const handleColleagueChange = (event) => {
        const colleagueId = event.target.value;
        setSelectedColleagueId(colleagueId);
        setSelectedColleagueShiftId('');
        setAllColleagueShifts([]);

        if (colleagueId) {
            // Arkadaşın TÜM vardiyalarını çekmek için ana vardiya listesini kullan
            // Bu API'yi zaten TakvimPage için yazmıştık
            axios.get('http://127.0.0.1:8000/api/schedules/vardiyalar/', getAuthHeaders())
                .then(response => {
                    const colleagueIdInt = parseInt(colleagueId, 10);
                    const shifts = response.data.filter(v => 
                        v.calisan === colleagueIdInt && // Sadece o arkadaşa ait olanlar
                        v.durum__in !== ['IPTAL', 'REDDEDILDI'] && // Aktif vardiyalar
                        new Date(v.baslangic_zamani) > new Date() // Sadece gelecekteki vardiyalar
                    );
                    setAllColleagueShifts(shifts);
                })
                .catch(err => setTradeError("Arkadaşın vardiyaları çekilemedi."));
        }
    };

    // Takas teklifini gönderir
    const handleSendTradeOffer = () => {
        setTradeError('');
        if (!selectedVardiya || !selectedColleagueShiftId) {
            setTradeError("Lütfen her iki vardiyayı da seçin."); return;
        }

        const dataToSend = {
            istek_yapan_vardiya: selectedVardiya.id,
            hedef_vardiya: parseInt(selectedColleagueShiftId),
            istek_yapan: currentUser.user_id,
            hedef_calisan: parseInt(selectedColleagueId)
        };

        axios.post(`http://127.0.0.1:8000/api/schedules/istekler/`, dataToSend, getAuthHeaders())
            .then(() => {
                alert("Takas teklifi başarıyla gönderildi!");
                handleCloseModal();
            })
            .catch(error => {
                console.error("Takas teklifi hatası!", error.response?.data || error.message);
                setTradeError(error.response?.data?.hata || 'Teklif gönderilemedi.');
            });
    };

    // ----------------------------

    // İptal Et fonksiyonu
    const handleIptalEt = (vardiya) => {
        if (!window.confirm(`${moment(vardiya.baslangic_zamani).format('DD MMM YYYY, HH:mm')} tarihli vardiyayı iptal etmek istediğinizden emin misiniz?`)) {
            return;
        }

        const dataToSend = {
            istek_yapan_vardiya: vardiya.id
        };

        axios.post(`http://127.0.0.1:8000/api/schedules/vardiya-iptal/`, dataToSend, getAuthHeaders())
            .then(() => {
                setSuccess("İptal isteğiniz admin onayına gönderildi.");
                fetchBenimVardiyalarim();
            })
            .catch(error => {
                console.error("İptal isteği hatası!", error.response?.data || error.message);
                setError(error.response?.data?.hata || 'İptal isteği gönderilemedi.');
            });
    };

    return (
        <Container maxWidth="lg" sx={{ mt: 4 }}>
            <Typography component="h1" variant="h4" gutterBottom>
                Gelecek Vardiyalarım
            </Typography>

            {loading && ( <Box sx={{ display: 'flex', justifyContent: 'center', my: 3 }}><CircularProgress /></Box> )}
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}

            {!loading && !error && (
                <TableContainer component={Paper}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>Tarih</TableCell>
                                <TableCell>Şube</TableCell>
                                <TableCell>Başlangıç</TableCell>
                                <TableCell>Bitiş</TableCell>
                                <TableCell align="right">İşlemler</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {vardiyalar.length === 0 && (
                                <TableRow><TableCell colSpan={5} align="center">Gelecek vardiyanız bulunmamaktadır.</TableCell></TableRow>
                            )}
                            {vardiyalar.map(vardiya => (
                                <TableRow key={vardiya.id}>
                                    <TableCell>{moment(vardiya.baslangic_zamani).format('DD MMM YYYY, dddd')}</TableCell>
                                    <TableCell>{vardiya.sube_adi}</TableCell>
                                    <TableCell>{moment(vardiya.baslangic_zamani).format('HH:mm')}</TableCell>
                                    <TableCell>{moment(vardiya.bitis_zamani).format('HH:mm')}</TableCell>
                                    <TableCell align="right">
                                        <Button
                                            variant="contained"
                                            onClick={() => handleTakasBaslat(vardiya)}
                                            sx={{ mr: 1 }}
                                        >
                                            Takas Et
                                        </Button>
                                        <Button
                                            variant="outlined"
                                            color="error"
                                            onClick={() => handleIptalEt(vardiya)}
                                        >
                                            İptal Et
                                        </Button>
                                    </TableCell>
                                </TableRow>
                            ))}
                        </TableBody>
                    </Table>
                </TableContainer>
            )}

            {/* --- YENİ TAKAS MODALI --- */}
            <Modal
                open={openModal}
                onClose={handleCloseModal}
                closeAfterTransition
                BackdropComponent={Backdrop}
                BackdropProps={{ timeout: 500 }}
            >
                <Fade in={openModal}>
                    <Box sx={modalStyle}>
                        <Typography variant="h6" component="h2" gutterBottom>Takas Teklifi Oluştur</Typography>
                        
                        {selectedVardiya && (
                            <Typography sx={{ mt: 2, mb: 2, p: 1, bgcolor: '#f0f0f0', borderRadius: 1 }}>
                                <strong>Teklif Edilen (Sizin):</strong><br/>
                                {moment(selectedVardiya.baslangic_zamani).format('DD MMM, HH:mm')} - {moment(selectedVardiya.bitis_zamani).format('HH:mm')}
                                ({selectedVardiya.sube_adi})
                            </Typography>
                        )}

                        <FormControl fullWidth sx={{ mt: 1 }}>
                            <InputLabel id="colleague-select-label">Adım 1: Çalışma Arkadaşı Seç</InputLabel>
                            <Select
                                labelId="colleague-select-label"
                                value={selectedColleagueId}
                                label="Adım 1: Çalışma Arkadaşı Seç"
                                onChange={handleColleagueChange}
                            >
                                <MenuItem value=""><em>Seçiniz...</em></MenuItem>
                                {colleagues.map(colleague => (
                                    <MenuItem key={colleague.id} value={colleague.id}>
                                        {colleague.first_name} {colleague.last_name} ({colleague.username})
                                    </MenuItem>
                                ))}
                            </Select>
                        </FormControl>

                        {selectedColleagueId && (
                            <FormControl component="fieldset" sx={{ mt: 2, maxHeight: 200, overflowY: 'auto', width: '100%', border: '1px solid #ccc', borderRadius: 1, p: 1 }}>
                                <Typography component="legend" sx={{ mb: 1 }}>Adım 2: Alınmak İstenen Vardiyayı Seç (Arkadaşınızın)</Typography>
                                {allColleagueShifts.length > 0 ? (
                                    <RadioGroup
                                        value={selectedColleagueShiftId}
                                        onChange={(e) => setSelectedColleagueShiftId(e.target.value)}
                                    >
                                        {allColleagueShifts.map(shift => (
                                            <FormControlLabel 
                                                key={shift.id} 
                                                value={shift.id.toString()} 
                                                control={<Radio />} 
                                                label={`${moment(shift.baslangic_zamani).format('DD MMM, HH:mm')} - ${moment(shift.bitis_zamani).format('HH:mm')} (${shift.sube_adi})`}
                                            />
                                        ))}
                                    </RadioGroup>
                                ) : (
                                    <Typography color="text.secondary" sx={{ p: 1 }}>Seçilen arkadaşınızın takas edilebilir bir gelecek vardiyası bulunmuyor.</Typography>
                                )}
                            </FormControl>
                        )}

                        {tradeError && <Alert severity="error" sx={{ mt: 2 }}>{tradeError}</Alert>}

                        <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                            <Button onClick={handleCloseModal} sx={{ mr: 1 }}>İptal</Button>
                            <Button
                                variant="contained"
                                onClick={handleSendTradeOffer}
                                disabled={!selectedColleagueShiftId}
                            >
                                Takas Teklifini Gönder
                            </Button>
                        </Box>
                    </Box>
                </Fade>
            </Modal>
            {/* ----------------------- */}
        </Container>
    );
}

export default VardiyalarimPage;