// src/pages/TakvimPage.js

import React, { useState, useEffect, useCallback } from 'react';
import { Calendar, momentLocalizer, Views } from 'react-big-calendar';
import moment from 'moment';
import 'moment/locale/tr';
import axios from 'axios';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { jwtDecode } from "jwt-decode";

import {
    Container, Typography, Button, Box, CircularProgress, Alert, Paper, Modal, Fade, Backdrop,
    Select, MenuItem, FormControl, InputLabel, RadioGroup, FormControlLabel, Radio
} from '@mui/material';

moment.locale('tr');
const localizer = momentLocalizer(moment);
const allViews = Object.keys(Views).map((k) => Views[k]);

const modalStyle = {
    position: 'absolute',
    top: '50%',
    left: '50%',
    transform: 'translate(-50%, -50%)',
    width: 400,
    bgcolor: 'background.paper',
    border: '2px solid #000',
    boxShadow: 24,
    p: 4,
    maxHeight: '90vh',
    overflowY: 'auto'
};

function TakvimPage() {
    const [events, setEvents] = useState([]);
    const [date, setDate] = useState(new Date());
    const [view, setView] = useState(Views.MONTH);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [error, setError] = useState('');
    const [successMessage, setSuccessMessage] = useState('');
    const [selectedEvent, setSelectedEvent] = useState(null);
    const [openModal, setOpenModal] = useState(false);
    const [currentUser, setCurrentUser] = useState(null);
    const [modalMode, setModalMode] = useState('detail');
    const [colleagues, setColleagues] = useState([]);
    const [selectedColleagueId, setSelectedColleagueId] = useState('');
    const [colleagueShifts, setColleagueShifts] = useState([]);
    const [selectedColleagueShiftId, setSelectedColleagueShiftId] = useState('');
    const [tradeError, setTradeError] = useState('');

    const getAuthHeaders = () => {
        const token = localStorage.getItem('accessToken');
        if (!token) {
            console.error("Auth token not found!");
            return {};
        }
        return { headers: { 'Authorization': `Bearer ${token}` } };
    };

    useEffect(() => {
        const token = localStorage.getItem('accessToken');
        if (token) {
            try { setCurrentUser(jwtDecode(token)); } catch (e) { console.error("Token error", e); }
        }
    }, []);

    const fetchVardiyalar = useCallback(() => {
        setLoading(true); setError('');
        axios.get('http://127.0.0.1:8000/api/schedules/vardiyalar/', getAuthHeaders())
            .then(response => {
                const formattedEvents = response.data.map(vardiya => ({
                    id: vardiya.id,
                    title: `${vardiya.calisan_adi} @ ${vardiya.sube_adi}`,
                    start: new Date(vardiya.baslangic_zamani),
                    end: new Date(vardiya.bitis_zamani),
                    resource: vardiya // Orijinal veriyi sakla (calisan ID'si burada)
                }));
                setEvents(formattedEvents);
            })
            .catch(error => { console.error("Vardiya fetch error!", error); setError('Vardiyalar yüklenemedi.'); })
            .finally(() => { setLoading(false); });
    }, []);

    useEffect(() => { fetchVardiyalar(); }, [fetchVardiyalar]);

    const fetchColleagues = useCallback(() => {
        if (!currentUser) return;
        axios.get('http://127.0.0.1:8000/api/kullanicilar/', getAuthHeaders())
            .then(response => {
                const others = response.data.filter(user => user.id !== currentUser.user_id);
                setColleagues(others);
            })
            .catch(error => console.error("Colleague fetch error!", error));
    }, [currentUser]);

    const handleNavigate = useCallback((newDate) => setDate(newDate), [setDate]);
    const handleViewChange = useCallback((newView) => setView(newView), [setView]);

    const handlePlanOlustur = () => {
        setGenerating(true); setError(''); setSuccessMessage('');
        const currentMonth = moment(date).format('YYYY-MM');
        axios.post('http://127.0.0.1:8000/api/schedules/plan-olustur/', { donem: currentMonth }, getAuthHeaders())
            .then(response => {
                setSuccessMessage(response.data.mesaj || 'Plan başarıyla oluşturuldu! Takvim yenileniyor...');
                fetchVardiyalar();
            })
            .catch(error => {
                console.error("Plan creation error!", error.response?.data?.hata || error.message);
                setError(error.response?.data?.hata || 'Plan oluşturulurken bir hata oluştu.');
            })
            .finally(() => { setGenerating(false); });
    };

    const handleSelectEvent = useCallback((event) => {
        const eventCalisanId = event.resource?.calisan;
        const loggedInUserId = currentUser?.user_id;

        // --- DÜZELTİLMİŞ KARŞILAŞTIRMA ---
        const isOwnShift = currentUser &&
                           eventCalisanId !== undefined &&
                           loggedInUserId !== undefined &&
                           parseInt(eventCalisanId, 10) === parseInt(loggedInUserId, 10);
        // ---------------------------------
        
        if (isOwnShift) {
            setSelectedEvent(event);
            setModalMode('detail'); setOpenModal(true); fetchColleagues();
            setTradeError(''); setSelectedColleagueId(''); setColleagueShifts([]); setSelectedColleagueShiftId('');
        } else {
             console.log("Başkasına ait vardiya seçildi (veya currentUser yok):", {
                vardiya_calisan_id: eventCalisanId,
                giris_yapan_id: loggedInUserId
             });
        }
    }, [currentUser, fetchColleagues]);

    const handleCloseModal = () => { setOpenModal(false); setSelectedEvent(null); };
    const handleInitiateTrade = () => { setModalMode('trade'); };

    const handleColleagueChange = (event) => {
        const colleagueId = event.target.value;
        setSelectedColleagueId(colleagueId);
        setSelectedColleagueShiftId(''); setColleagueShifts([]);

        if (colleagueId && selectedEvent) {
            const targetDate = moment(selectedEvent.start).format('YYYY-MM-DD');
            const colleagueIdInt = parseInt(colleagueId, 10);
            const shifts = events.filter(e =>
                e.resource?.calisan === colleagueIdInt &&
                moment(e.start).format('YYYY-MM-DD') === targetDate
            );
            setColleagueShifts(shifts);
        }
    };

     const handleSendTradeOffer = () => {
        setTradeError('');
        if (!selectedEvent || !selectedColleagueShiftId) {
            setTradeError("Lütfen her iki vardiyayı da seçin."); return;
        }

        const dataToSend = {
            istek_yapan_vardiya: selectedEvent.resource.id,
            hedef_vardiya: parseInt(selectedColleagueShiftId),
            istek_yapan: currentUser.user_id,
            hedef_calisan: parseInt(selectedColleagueId)
        };

        axios.post(`http://127.0.0.1:8000/api/schedules/istekler/`, dataToSend, getAuthHeaders())
            .then(() => {
                setSuccessMessage("Takas teklifi başarıyla gönderildi!");
                handleCloseModal();
            })
            .catch(error => {
                console.error("Trade offer error!", error.response?.data || error.message);
                setTradeError(error.response?.data?.hata || error.response?.data?.detail || 'Takas teklifi gönderilemedi.');
            });
    };

    return (
        <Container maxWidth="xl" sx={{ mt: 4 }}>
             <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography component="h1" variant="h4">Vardiya Planı Takvimi</Typography>
                <Button variant="contained" onClick={handlePlanOlustur} disabled={generating || loading}>
                    {generating ? <CircularProgress size={24} /> : `${moment(date).format('MMMM YYYY')} Planını Oluştur`}
                </Button>
            </Box>
            {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
            {successMessage && <Alert severity="success" sx={{ mb: 2 }}>{successMessage}</Alert>}

            <Paper sx={{ height: '75vh', p: 2 }}>
                {loading ? ( <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}><CircularProgress /><Typography sx={{ ml: 2 }}>Yükleniyor...</Typography></Box> ) : (
                    <Calendar
                        localizer={localizer} events={events} startAccessor="start" endAccessor="end"
                        date={date} onNavigate={handleNavigate} onSelectEvent={handleSelectEvent}
                        view={view} onView={handleViewChange} views={allViews}
                        messages={{next: "İleri", previous: "Geri", today: "Bugün", month: "Ay", week: "Hafta", day: "Gün", agenda: "Ajanda"}}
                        style={{ height: '100%' }}
                    />
                )}
            </Paper>

            <Modal
                open={openModal}
                onClose={handleCloseModal}
                closeAfterTransition
                BackdropComponent={Backdrop}
                BackdropProps={{ timeout: 500 }}
            >
                <Fade in={openModal}>
                    <Box sx={modalStyle}>
                        {modalMode === 'detail' && selectedEvent && (
                            <>
                                <Typography variant="h6" component="h2" gutterBottom>Vardiya Detayları</Typography>
                                <Typography sx={{ mt: 2 }}><strong>Başlangıç:</strong> {moment(selectedEvent.start).format('DD MMM YYYY, HH:mm')}</Typography>
                                <Typography><strong>Bitiş:</strong> {moment(selectedEvent.end).format('DD MMM YYYY, HH:mm')}</Typography>
                                <Typography><strong>Detay:</strong> {selectedEvent.title}</Typography>
                                <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                                    <Button onClick={handleCloseModal} sx={{ mr: 1 }}>Kapat</Button>
                                    <Button variant="contained" onClick={handleInitiateTrade}>Takas Teklif Et</Button>
                                </Box>
                            </>
                        )}

                        {modalMode === 'trade' && selectedEvent && (
                            <>
                                <Typography variant="h6" component="h2" gutterBottom>Takas Teklifi Oluştur</Typography>
                                <Typography sx={{ mt: 2 }}>
                                    <strong>Teklif Edilen (Sizin):</strong><br/>
                                    {moment(selectedEvent.start).format('DD MMM, HH:mm')} - {moment(selectedEvent.end).format('HH:mm')} ({selectedEvent.resource.sube_adi})
                                </Typography>

                                <FormControl fullWidth sx={{ mt: 2 }}>
                                    <InputLabel id="colleague-select-label">Kimle Takas Etmek İstersiniz?</InputLabel>
                                    <Select labelId="colleague-select-label" value={selectedColleagueId} label="Kimle Takas Etmek İstersiniz?" onChange={handleColleagueChange}>
                                        <MenuItem value=""><em>Seçiniz...</em></MenuItem>
                                        {colleagues.map(colleague => ( <MenuItem key={colleague.id} value={colleague.id}>{colleague.first_name} {colleague.last_name} ({colleague.username})</MenuItem> ))}
                                    </Select>
                                </FormControl>

                                {selectedColleagueId && colleagueShifts.length > 0 && (
                                    <FormControl component="fieldset" sx={{ mt: 2, maxHeight: 150, overflowY: 'auto', width: '100%' }}>
                                        <Typography><strong>Alınmak İstenen (Arkadaşınızın - {moment(selectedEvent.start).format('DD MMM')}):</strong></Typography>
                                        <RadioGroup value={selectedColleagueShiftId} onChange={(e) => setSelectedColleagueShiftId(e.target.value)}>
                                            {colleagueShifts.map(shift => ( <FormControlLabel key={shift.id} value={shift.resource.id.toString()} control={<Radio />} label={`${moment(shift.start).format('HH:mm')} - ${moment(shift.end).format('HH:mm')} (${shift.resource.sube_adi})`}/> ))}
                                        </RadioGroup>
                                    </FormControl>
                                )}
                                {selectedColleagueId && colleagueShifts.length === 0 && ( <Typography sx={{ mt: 2 }} color="text.secondary">Seçilen arkadaşınızın o gün başka vardiyası yok.</Typography> )}

                                {tradeError && <Alert severity="error" sx={{ mt: 2 }}>{tradeError}</Alert>}

                                <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                                    <Button onClick={() => setModalMode('detail')} sx={{ mr: 1 }}>Geri</Button>
                                    <Button variant="contained" onClick={handleSendTradeOffer} disabled={!selectedColleagueShiftId}>Teklifi Gönder</Button>
                                </Box>
                            </>
                        )}
                    </Box>
                </Fade>
            </Modal>
        </Container>
    );
}

export default TakvimPage;