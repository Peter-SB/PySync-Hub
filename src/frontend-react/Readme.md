# Frontend React Technical Readme
PySync Hub's frontend is built with React using modern JavaScript practices and follows a component-based architecture. While I initially chose HTMX SSR for a basic UI, as the program grew and became more dynamic I was forced to upgrade to React. 

## Key Frontend Features
### Data Fetching and State Management With React Query
React Query was a massive help with this project especially dues to the dynamic nature and need for optimistic UI rendering. I use custom hooks to abstract data fetching and do state management:

`usePlaylists` - Encapsulates playlist data fetching and caching
`usePlaylistMutations` - Handles playlist CRUD operations
`useFolders/useFolderMutations` - Same for Folder
`useSocketPlaylistUpdates` - Handles WebSockets

This approach ensures components remain focused on presentation while data management logic is centralised and reusable.

### Intuitive Drag and Drop Interface with dnd-kit
To make the folder management feel really sleek and intuitive I used React dnd-kit for adding this interface. [Read More Here](https://github.com/Peter-SB/dnd-kit-folder-demo).

This truly made me appreciate the effort that goes into some UI elements and how well done, it wont be noticed at all.

### Real-time Webhook Updates
Websockets were chose for realtime communication between the front end back end. They allow for:

Download progress updates
Export status notifications
Playlist and track changes

This provides immediate feedback to users during this long-running program without needing constant polling.

## Key Design Patterns & Principles
* Component Composition: Building complex UIs from simpler ones
* Custom Hooks: Extracting and sharing stateful logic between components
* Context API: For global error state that needs to be accessed by many components
* Container/Presentational Pattern: Separating data fetching from presentation
* Responsive Design: Using Tailwind CSS intuitive inline styling

## Notable Technical Details
* WebSocket Integration: Real-time communication with the Flask backend
* State Management: With React Query for caching and optimistic UI updates
* Drag and Drop Organisation