import { Routes } from '@angular/router';
import { Default } from './views/default/default';
import { Login } from './views/login/login';
import { Album } from './views/album/album';
import { authGuard } from './services/guard';
import { Join } from './views/join/join';
import { Myprofile } from './views/myprofile/myprofile';
import { Updateprofile } from './views/updateprofile/updateprofile';
import { Logout } from './views/logout/logout';
import { Passrecover } from './views/passrecover/passrecover';
import { ControlPanel } from './views/control-panel/control-panel';

export const routes: Routes = [
    { path: '', redirectTo: 'default', pathMatch: "full" },
    { path: 'default', component: Default },
    { path: 'login', component: Login },
    { path: 'newuser', component: Join},
    { path: 'profile', component: Myprofile, canActivate: [authGuard] },
    { path: 'album', component: Album, canActivate: [authGuard]},
    { path: 'updateprofile', component: Updateprofile, canActivate: [authGuard] },
    { path: 'logout', component: Logout, canActivate: [authGuard] },
    { path: 'passrecover', component: Passrecover },
    { path: 'panel', component: ControlPanel, canActivate: [authGuard] }
];
