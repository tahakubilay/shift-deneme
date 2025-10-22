// src/pages/BranchListPage.js

import React, { useState, useEffect } from 'react';
import axios from 'axios';

// --- MUI Bileşenlerini ve İkonları Import Ediyoruz ---
import { 
    Button, TextField, Container, Typography, Box, Alert,
    Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper, IconButton,
    Modal, Fade, Backdrop 
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
// ----------------------------------------------------

// Modal için stil objesi
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
};


function BranchListPage() {
    const [subeler, setSubeler] = useState([]);
    const [yeniSubeAdi, setYeniSubeAdi] = useState('');
    const [yeniAdres, setYeniAdres] = useState('');
    
    // Düzenleme modal'ını yönetmek için state'ler
    const [editingSube, setEditingSube] = useState(null); // Düzenlenen şubeyi tutar
    const [updatedAdi, setUpdatedAdi] = useState('');
    const [updatedAdres, setUpdatedAdres] = useState('');

    const getAuthHeaders = () => {
        const token = localStorage.getItem('accessToken');
        return { headers: { 'Authorization': `Bearer ${token}` } };
    };

    useEffect(() => {
        fetchSubeler();
    }, []);

    const fetchSubeler = () => {
        axios.get('http://127.0.0.1:8000/api/subeler/', getAuthHeaders())
            .then(response => setSubeler(response.data))
            .catch(error => console.error("Şube verisi çekilirken hata!", error));
    };

    const handleSubmit = (event) => {
        event.preventDefault();
        const yeniSube = { sube_adi: yeniSubeAdi, adres: yeniAdres };
        axios.post('http://127.0.0.1:8000/api/subeler/', yeniSube, getAuthHeaders())
            .then(response => {
                setSubeler([...subeler, response.data]);
                setYeniSubeAdi('');
                setYeniAdres('');
            })
            .catch(error => console.error("Şube eklenirken bir hata oluştu!", error));
    };

    const handleDelete = (subeId) => {
        if (window.confirm("Bu şubeyi silmek istediğinizden emin misiniz?")) {
            axios.delete(`http://127.0.0.1:8000/api/subeler/${subeId}/`, getAuthHeaders())
                .then(() => {
                    setSubeler(subeler.filter(sube => sube.id !== subeId));
                })
                .catch(error => console.error("Şube silinirken hata!", error));
        }
    };

    const handleEditClick = (sube) => {
        setEditingSube(sube);
        setUpdatedAdi(sube.sube_adi);
        setUpdatedAdres(sube.adres);
    };

    const handleUpdate = (event) => {
        event.preventDefault();
        const guncelSube = { sube_adi: updatedAdi, adres: updatedAdres };
        axios.put(`http://127.0.0.1:8000/api/subeler/${editingSube.id}/`, guncelSube, getAuthHeaders())
            .then(response => {
                setSubeler(subeler.map(sube => sube.id === editingSube.id ? response.data : sube));
                setEditingSube(null); // Modalı kapat
            })
            .catch(error => console.error("Şube güncellenirken hata!", error));
    };

    return (
        <Container maxWidth="md" sx={{ mt: 4 }}>
            <Typography component="h1" variant="h4" gutterBottom>
                Şube Yönetimi
            </Typography>

            {/* Yeni Şube Ekleme Formu */}
            <Paper sx={{ p: 2, mb: 3 }}>
                <Typography variant="h6">Yeni Şube Ekle</Typography>
                <Box component="form" onSubmit={handleSubmit} sx={{ display: 'flex', gap: 2, mt: 1 }}>
                    <TextField label="Şube Adı" value={yeniSubeAdi} onChange={e => setYeniSubeAdi(e.target.value)} required fullWidth />
                    <TextField label="Adres" value={yeniAdres} onChange={e => setYeniAdres(e.target.value)} required fullWidth />
                    <Button type="submit" variant="contained">Ekle</Button>
                </Box>
            </Paper>

            {/* Şube Listesi Tablosu */}
            <TableContainer component={Paper}>
                <Table>
                    <TableHead>
                        <TableRow>
                            <TableCell>Şube Adı</TableCell>
                            <TableCell>Adres</TableCell>
                            <TableCell align="right">İşlemler</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {subeler.map(sube => (
                            <TableRow key={sube.id}>
                                <TableCell>{sube.sube_adi}</TableCell>
                                <TableCell>{sube.adres}</TableCell>
                                <TableCell align="right">
                                    <IconButton onClick={() => handleEditClick(sube)} color="primary">
                                        <EditIcon />
                                    </IconButton>
                                    <IconButton onClick={() => handleDelete(sube.id)} color="error">
                                        <DeleteIcon />
                                    </IconButton>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </TableContainer>

            {/* Düzenleme Modalı */}
            <Modal
                open={Boolean(editingSube)}
                onClose={() => setEditingSube(null)}
                closeAfterTransition
                BackdropComponent={Backdrop}
                BackdropProps={{ timeout: 500 }}
            >
                <Fade in={Boolean(editingSube)}>
                    <Box sx={modalStyle}>
                        <Typography variant="h6" component="h2">Şubeyi Düzenle</Typography>
                        <Box component="form" onSubmit={handleUpdate} sx={{ mt: 2 }}>
                            <TextField label="Şube Adı" value={updatedAdi} onChange={e => setUpdatedAdi(e.target.value)} required fullWidth sx={{ mb: 2 }}/>
                            <TextField label="Adres" value={updatedAdres} onChange={e => setUpdatedAdres(e.target.value)} required fullWidth />
                            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
                                <Button onClick={() => setEditingSube(null)} sx={{ mr: 1 }}>İptal</Button>
                                <Button type="submit" variant="contained">Kaydet</Button>
                            </Box>
                        </Box>
                    </Box>
                </Fade>
            </Modal>
        </Container>
    );
}

export default BranchListPage;