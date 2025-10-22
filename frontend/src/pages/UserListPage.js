// src/pages/UserListPage.js

import React, { useState, useEffect } from 'react';
import axios from 'axios';

// --- MUI Bileşenlerini ve İkonları Import Ediyoruz ---
import {
    Container, Typography, Box,
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, IconButton
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
// ----------------------------------------------------

function UserListPage() {
    const [kullanicilar, setKullanicilar] = useState([]);

    useEffect(() => {
        const token = localStorage.getItem('accessToken');
        axios.get('http://127.0.0.1:8000/api/kullanicilar/', {
            headers: { 'Authorization': `Bearer ${token}` }
        })
        .then(response => {
            setKullanicilar(response.data);
        })
        .catch(error => console.error("Kullanıcı verisi çekilirken hata!", error));
    }, []);

    return (
        <Container maxWidth="lg" sx={{ mt: 4 }}>
            <Typography component="h1" variant="h4" gutterBottom>
                Kullanıcı Yönetimi
            </Typography>

            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Ad Soyad</TableCell>
                            <TableCell>Kullanıcı Adı</TableCell>
                            <TableCell>E-posta</TableCell>
                            <TableCell>Rol</TableCell>
                            <TableCell>Telefon</TableCell>
                            <TableCell align="right">İşlemler</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {kullanicilar.map(user => (
                            <TableRow key={user.id}>
                                <TableCell>{user.first_name} {user.last_name}</TableCell>
                                <TableCell>{user.username}</TableCell>
                                <TableCell>{user.email}</TableCell>
                                <TableCell>{user.rol}</TableCell>
                                <TableCell>{user.telefon}</TableCell>
                                <TableCell align="right">
                                    {/* İleride bu butonların fonksiyonlarını ekleyeceğiz */}
                                    <IconButton disabled color="primary">
                                        <EditIcon />
                                    </IconButton>
                                    <IconButton disabled color="error">
                                        <DeleteIcon />
                                    </IconButton>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>
        </Container>
    );
}

export default UserListPage;