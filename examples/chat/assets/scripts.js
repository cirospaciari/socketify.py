
function get_room(name, token, on_history, on_message){

    const ws = new WebSocket(`ws://localhost:3000?room=${name}&token=${token}`);
    var status = 'pending';
    const connection = new Promise((resolve)=>{
        ws.onopen = function(){
            status = 'connected';
            resolve(true)
        }
        ws.onerror = function(){
            status = 'error';
            resolve(false)
        }   
    });

    ws.onclose = function(){
        status = 'closed';
    }
    ws.onmessage = (event) => {
       const message = JSON.parse(event.data);  
        if(message instanceof Array){
            on_history(message)
        }else{
            on_message(message)
        }
    }

    return {
        send(message){
            ws.send(JSON.stringify(message));
        },
        wait_connection(){
            return connection;
        },
        is_connected(){
            return status === 'connected';
        },
        close(){
            ws.close()
        }
    }
}

function get_utc_date(){
    return new Date().toLocaleTimeString('en-US', { hour12:false, hour: '2-digit', minute: '2-digit', timeZone: 'UTC', timeZoneName: 'short' })
}

function get_session() {
    let name = "session=";
    let decodedCookie = decodeURIComponent(document.cookie);
    let ca = decodedCookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') {
            c = c.substring(1);
        }
        if (c.indexOf(name) == 0) {
            return c.substring(name.length, c.length);
        }
    }
    return "";
}

async function get_user() {
    const session = get_session()
    if (!session) return null;
    try {
        const response = await fetch('https://api.github.com/user', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${session}`,
                'Accept': 'application/json'
            }
        })
        return await response?.json()
    } catch (err) {
        console.error(err);
        return null;
    }
}

function request_login(){
    return document.location.href = 'https://github.com/login/oauth/authorize?scope=user:email&client_id=9481803176fb73d616b7';
}
let current_room = null;
let last_room_name = 'general';
async function send_message(event){
    if(event && event.key?.toLowerCase() !== 'enter') return;
    
    const message = document.querySelector("#chat-message");
    await current_room?.wait_connection();
    if(current_room?.is_connected()){
        current_room.send({
            text: message.value,
            datetime: get_utc_date()
        })
        //clean
        message.value = ''
    }else {
        await open_room(last_room_name)
        send_message();
    }
}

async function open_room(name){
    last_room_name = name;
    const user = await get_user();
    if(!user){
        return request_login();
    }
    const chat = document.querySelector('.chat-messages');
    
    const room = get_room(name, get_session(), (history)=> {
        //clear
        chat.innerHTML = '';
        //add messages
        for(let message of history){
            chat.appendChild(format_message(message, user));
        }
        chat.scroll(0, chat.scrollHeight)
    }, (message)=>{
        //add message
        chat.appendChild(format_message(message, user));

        //trim size
        while(chat.childNodes.length > 100){
            chat.firstChild.remove();
        }
        chat.scroll(0, chat.scrollHeight)
    });
    await room.wait_connection()
    current_room = room;
}
const markdown = new showdown.Converter({simpleLineBreaks: true,openLinksInNewWindow: true, emoji: true, ghMentions: true, tables: true, strikethrough: true, tasklists: true});

function format_message(message, user){
    const message_element = document.createElement("div");
    if(message.login === user.login){
        message.name = 'You';
        message_element.classList.add('chat-message-right');
    }else{
        message_element.classList.add('chat-message-left'); 
    }
    
    message_element.classList.add('pb-4');
    
    const header = document.createElement("div");
    image = new Image(40, 40);
    image.src = message.avatar_url;
    image.classList.add('rounded-circle');
    image.classList.add('mr-1');
    image.alt = message.name;

    const date = document.createElement("div");
    date.classList.add('text-muted');
    date.classList.add('small');
    date.classList.add('text-nowrap');
    date.classList.add('mt-2');
    date.textContent = message.datetime;
    header.addEventListener("click", ()=> {
        window.open(message.html_url, '_blank').focus();
    });
    header.appendChild(image);
    header.appendChild(date);

    message_element.appendChild(header);

    const body = document.createElement("div");
    body.classList.add('flex-shrink-1');
    body.classList.add('bg-light');
    body.classList.add('rounded');
    body.classList.add('py-2');
    body.classList.add('px-3');
    body.classList.add('mr-3');
    
    const author = document.createElement("div")
    author.classList.add('font-weight-bold');
    author.classList.add('mb-1');
    author.textContent = message.name;
    
    
    body.appendChild(author);
    const content = document.createElement("div");
    content.innerHTML = markdown.makeHtml(message.text);
    body.appendChild(content);
    
    message_element.appendChild(body);

    return message_element;
}

get_user().then((is_logged_in)=>{
    if(is_logged_in){
         open_room("general");
    }
 }); 