// src/pages/TakvimPage.js

import React, { useState, useEffect, useCallback } from 'react';
import { Calendar, momentLocalizer } from 'react-big-calendar';
import moment from 'moment';
import 'moment/locale/tr';
import axios from 'axios';

import 'react-big-calendar/lib/css/react-big-calendar.css';

moment.locale('tr');
const localizer = momentLocalizer(moment);

function TakvimPage() {
    const [events, setEvents] = useState([]);
    const [date, setDate] = useState(new Date());

    // --- EKSİK OLAN YARDIMCI FONKSİYONU EKLEYİN ---
    const getAuthHeaders = () => {
        const token = localStorage.getItem('accessToken');
        return { headers: { 'Authorization': `Bearer ${token}` } };
    };
    // -----------------------------------------

    useEffect(() => {
        // --- API ÇAĞRISINI GÜNCELLEYİN ---
        axios.get('http://127.0.0.1:8000/api/schedules/vardiyalar/', getAuthHeaders())
            .then(response => {
                const formattedEvents = response.data.map(vardiya => ({
                    id: vardiya.id,
                    title: `${vardiya.calisan} - ${vardiya.sube}`,
                    start: new Date(vardiya.baslangic_zamani),
                    end: new Date(vardiya.bitis_zamani),
                }));
                setEvents(formattedEvents);
            })
            .catch(error => console.error("Vardiya verileri çekilirken hata!", error));
    }, []);

    const handleNavigate = useCallback((newDate) => setDate(newDate), [setDate]);

    return (
        <div style={{ height: '80vh', padding: '20px' }}>
            <h1>Vardiya Planı Takvimi</h1>
            <Calendar
                localizer={localizer}
                events={events}
                startAccessor="start"
                endAccessor="end"
                date={date}
                onNavigate={handleNavigate}
                messages={{
                    next: "İleri",
                    previous: "Geri",
                    today: "Bugün",
                    month: "Ay",
                    week: "Hafta",
                    day: "Gün"
                }}
            />
        </div>
    );
}

export default TakvimPage;