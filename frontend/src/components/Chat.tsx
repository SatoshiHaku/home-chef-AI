import React, { useState, useRef, useEffect } from 'react';
import { Box, TextField, IconButton, Paper, Typography, List, ListItem, ListItemText, Divider } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  ingredients?: Array<{
    name: string;
    quantity: number;
    unit: string;
    expiry_date?: string;
    category: string;
  }>;
  recipes?: Array<{
    id: string;
    name: string;
    ingredients: Array<{
      name: string;
      quantity: number;
      unit: string;
    }>;
    steps: Array<{
      step: number;
      description: string;
    }>;
    url: string;
    source: string;
    last_cooked?: string;
  }>;
}

const Chat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<null | HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const formatMessage = (message: Message) => {
    const ingredients = message.ingredients ?? [];
    const recipes = message.recipes ?? [];

    if (ingredients.length > 0) {
      return (
        <Box>
          <Typography variant="body1">{message.content}</Typography>
          <List>
            {ingredients.map((ingredient, index) => (
              <React.Fragment key={index}>
                <ListItem>
                  <ListItemText
                    primary={`${ingredient.name} (${ingredient.quantity}${ingredient.unit})`}
                    secondary={`カテゴリー: ${ingredient.category}${ingredient.expiry_date ? `, 消費期限: ${ingredient.expiry_date}` : ''}`}
                  />
                </ListItem>
                {index < ingredients.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </Box>
      );
    }

    if (recipes.length > 0) {
      return (
        <Box>
          <Typography variant="body1">{message.content}</Typography>
          <List>
            {recipes.map((recipe, index) => (
              <React.Fragment key={index}>
                <ListItem>
                  <ListItemText
                    primary={recipe.name}
                    secondary={
                      <Box>
                        <Typography variant="body2">材料:</Typography>
                        <List dense>
                          {recipe.ingredients.map((ing, i) => (
                            <ListItem key={i}>
                              <ListItemText
                                primary={`${ing.name} (${ing.quantity}${ing.unit})`}
                              />
                            </ListItem>
                          ))}
                        </List>
                        <Typography variant="body2">手順:</Typography>
                        <List dense>
                          {recipe.steps.map((step, i) => (
                            <ListItem key={i}>
                              <ListItemText
                                primary={`${step.step}. ${step.description}`}
                              />
                            </ListItem>
                          ))}
                        </List>
                        <Typography variant="body2">
                          出典: {recipe.source}
                          {recipe.last_cooked ? `, 最終調理: ${recipe.last_cooked}` : ''}
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
                {index < recipes.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </List>
        </Box>
      );
    }

    return <Typography variant="body1">{message.content}</Typography>;
  };

  const handleSend = async () => {
    if (!input.trim()) return;

    const newMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, newMessage]);
    setInput('');

    try {
      const response = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [...messages, newMessage],
        }),
      });

      const data = await response.json();
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: data.message,
        ingredients: data.ingredients,
        recipes: data.recipes
      }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: '申し訳ありません。エラーが発生しました。' 
      }]);
    }
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      <Box sx={{ flexGrow: 1, overflow: 'auto', p: 2 }}>
        {messages.map((message, index) => (
          <Paper
            key={index}
            sx={{
              p: 2,
              mb: 2,
              backgroundColor: message.role === 'user' ? '#e3f2fd' : '#f5f5f5',
              maxWidth: '80%',
              ml: message.role === 'user' ? 'auto' : 0,
            }}
          >
            {formatMessage(message)}
          </Paper>
        ))}
        <div ref={messagesEndRef} />
      </Box>
      <Box sx={{ p: 2, backgroundColor: 'background.paper' }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            variant="outlined"
            placeholder="メッセージを入力..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          />
          <IconButton color="primary" onClick={handleSend}>
            <SendIcon />
          </IconButton>
        </Box>
      </Box>
    </Box>
  );
};

export default Chat; 