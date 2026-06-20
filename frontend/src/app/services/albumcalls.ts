import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { Tokenresponse } from '../models/tokenresponse.interface';
import { Photoresponse } from '../models/photoresponse.interface';
import { Newuser } from '../models/newuser.interface';
import { Userresponse } from '../models/userresponse.interface';

@Injectable({
  providedIn: 'root',
})
export class Albumcalls {
  private http = inject(HttpClient)


  //===================> GET <=======================\\

  public getPhoto(url:string): Observable<Photoresponse> {
    return this.http.get<Photoresponse>(url);
  }

  public getPhotos(url:string): Observable<Photoresponse[]> {
    return this.http.get<Photoresponse[]>(url);
  }

  public getMyPhotos(url:string): Observable<Photoresponse[]> {
    return this.http.get<Photoresponse[]>(url);
  }

  public getUsers(url:string): Observable<Userresponse[]> {
    return this.http.get<Userresponse[]>(url)
  }

  //===> Obtiene los datos del usuario logueado <=========\\
  public getUser(url:string): Observable<Userresponse> {
    const headers = new HttpHeaders({
      'accept': 'application/json'
    })
    return this.http.get<Userresponse>(url, { headers })
  }

  public getDisabledUsers(url:string): Observable<Userresponse[]> {
    const headers = new HttpHeaders({
      'accept': 'application/json'
    })
    return this.http.get<Userresponse[]>(url, { headers })
  }

  public enableUser(url:string): Observable<any> {
    const headers = new HttpHeaders({
      'accept': 'application/json'
    })
    return this.http.patch<any>(url, {}, { headers })
  }

  public getPhotosByTitle(url:string): Observable<Photoresponse[]> {
    return this.http.get<Photoresponse[]>(url);
  }

  public getPhotosByTag(url:string): Observable<Photoresponse[]> {
    return this.http.get<Photoresponse[]>(url);
  }

  //===================> POST <=======================\\

      //Para conseguir(get) un token necesitaremos hacer un post.
  public getToken(url:string, body:HttpParams): Observable<Tokenresponse> {
    const headers = new HttpHeaders({
      'Content-Type': 'application/x-www-form-urlencoded',
      'accept': 'application/json',
      'body': ''
    })
    return this.http.post<Tokenresponse>(url,body, { headers })
  }


  public createUser(url:string, body:Newuser): Observable<any> {
    const headers = new HttpHeaders({
      'accept': 'application/json'
    })
    return this.http.post<any>(url,body, { headers });
  }

  public createPhoto(url:string, body:any): Observable<any> {
    const headers = new HttpHeaders({
      'accept': 'application/json'
    })
    return this.http.post<any>(url,body, { headers });
  }

  public recoverPassword(url:string,email: string): Observable<any> {
    return this.http.post(url, { email: email });
  }

  public validatePassword(url:string, token: string, newPassword: string): Observable<any> {
    // Enviamos el token en el body para evitar conflictos con el interceptor de Bearer
    return this.http.post(url, { 
      token: token, 
      new_password: newPassword 
    });
  }

  //=====================> DELETE <=====================\\

  public deletePhoto(url:string): Observable<any> {
    const headers = new HttpHeaders({
      'accept': 'application/json'
    })
    return this.http.delete<any>(url);
  }

  public deleteUser(url:string): Observable<any> {
    const headers = new HttpHeaders({
      'accept': 'application/json'
    })
    return this.http.delete<any>(url);
  }


  //======================> UPDATE <=====================\\
  public patchPhoto(url:string,body: Record<string, unknown>): Observable<any> {
    const headers = new HttpHeaders({
      'accept': 'application/json',
      'Content-Type': 'application/json'
    })
    return this.http.patch<any>(url,body,{ headers })
  }

  public patchUser(url:string,body:any): Observable<any> {
    const headers = new HttpHeaders({
      'accept': 'application/json'
    })
    return this.http.patch<any>(url,body,{ headers })
  }
}

