import React, { useState, useRef } from 'react';
import {
  Box,
  Button,
  Avatar,
  Typography,
  Alert,
  CircularProgress,
  Paper,
  IconButton,
} from '@mui/material';
import { CloudUpload, Delete, Edit } from '@mui/icons-material';
import { useSelector, useDispatch } from 'react-redux';
import { useTheme } from '@mui/material/styles';
import { RootState } from '../../store';
import { uploadProfilePicture, deleteProfilePicture } from '../../store/slices/userProfileSlice';

const ProfilePictureUpload: React.FC = () => {
  const theme = useTheme();
  const dispatch = useDispatch<any>();
  const { user } = useSelector((state: RootState) => state.auth);
  const { loading, error } = useSelector((state: RootState) => state.userProfile || {});

  const [preview, setPreview] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'].join(',');
  const MAX_SIZE = 5 * 1024 * 1024; // 5MB

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    // Validate file type
    if (!['image/jpeg', 'image/png', 'image/gif', 'image/webp'].includes(file.type)) {
      setUploadError('Please select a valid image file (JPEG, PNG, GIF, or WebP)');
      return;
    }

    // Validate file size
    if (file.size > MAX_SIZE) {
      setUploadError('File size must be less than 5MB');
      return;
    }

    setUploadError('');
    setSelectedFile(file);

    // Create preview
    const reader = new FileReader();
    reader.onload = e => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      return;
    }

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      await dispatch(uploadProfilePicture(formData));
      setPreview(null);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (err) {
      console.error('Upload failed:', err);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to remove your profile picture?')) {
      await dispatch(deleteProfilePicture());
    }
  };

  const handleCancelPreview = () => {
    setPreview(null);
    setSelectedFile(null);
    setUploadError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const openFileDialog = () => {
    fileInputRef.current?.click();
  };

  if (!user) {
    return (
      <Typography variant="body1" color="textSecondary">
        Please log in to upload a profile picture.
      </Typography>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
        Profile Picture
      </Typography>

      {(error || uploadError) && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error || uploadError}
        </Alert>
      )}

      <Paper
        elevation={1}
        sx={{
          p: 3,
          textAlign: 'center',
          border: `2px dashed ${theme.palette.divider}`,
          borderRadius: 2,
          bgcolor: 'background.paper',
        }}
      >
        <Box sx={{ mb: 3 }}>
          <Avatar
            src={preview || user.profile_picture_url || undefined}
            sx={{
              width: 120,
              height: 120,
              mx: 'auto',
              mb: 2,
              bgcolor: theme.palette.primary.main,
              fontSize: '3rem',
            }}
          >
            {!preview && !user.profile_picture_url && user.username.charAt(0).toUpperCase()}
          </Avatar>

          {user.profile_picture_url && !preview && (
            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center', mb: 2 }}>
              <IconButton
                onClick={openFileDialog}
                disabled={loading}
                color="primary"
                aria-label="Change profile picture"
              >
                <Edit />
              </IconButton>
              <IconButton
                onClick={handleDelete}
                disabled={loading}
                color="error"
                aria-label="Delete profile picture"
              >
                <Delete />
              </IconButton>
            </Box>
          )}
        </Box>

        {preview ? (
          <Box>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
              Ready to upload: {selectedFile?.name}
            </Typography>
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
              <Button
                variant="contained"
                onClick={handleUpload}
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : <CloudUpload />}
              >
                {loading ? 'Uploading...' : 'Upload'}
              </Button>
              <Button variant="outlined" onClick={handleCancelPreview} disabled={loading}>
                Cancel
              </Button>
            </Box>
          </Box>
        ) : (
          <Box>
            <CloudUpload
              sx={{
                fontSize: 48,
                color: theme.palette.text.secondary,
                mb: 2,
                display: 'block',
                mx: 'auto',
              }}
            />
            <Typography variant="body1" gutterBottom>
              Click to upload a profile picture
            </Typography>
            <Typography variant="body2" color="textSecondary" sx={{ mb: 3 }}>
              Supports JPEG, PNG, GIF, WebP up to 5MB
            </Typography>
            <Button
              variant="contained"
              onClick={openFileDialog}
              disabled={loading}
              startIcon={<CloudUpload />}
            >
              Choose File
            </Button>
          </Box>
        )}

        <input
          ref={fileInputRef}
          type="file"
          accept={ALLOWED_TYPES}
          onChange={handleFileSelect}
          style={{ display: 'none' }}
        />
      </Paper>

      <Typography variant="caption" display="block" sx={{ mt: 2, textAlign: 'center' }}>
        Your profile picture will be visible to other users and in your account settings.
      </Typography>
    </Box>
  );
};

export default ProfilePictureUpload;
